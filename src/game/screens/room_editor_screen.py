"""Grid-based room authoring using the same Room renderer as combat."""
from copy import deepcopy
import random
import pygame
from game.screens.base_screen import BaseScreen
from game.ui.fonts import create_font
from game.rooms.room_data import tower_room, NORMAL_ROOMS, BOSS_ROOMS
from game.rooms.custom_rooms import documents, save_room, validate, delete_room
from game.rooms.room import Room


class RoomEditorScreen(BaseScreen):
    VIRTUAL_WIDTH = 640
    VIRTUAL_HEIGHT = 360
    CELL = 22
    GRID = pygame.Rect(169, 46, 286, 242)
    TILES = ['.', ' ', 'O', 'V', 'P', 'E', 'B']
    COLORS = {'.': (74, 85, 88), ' ': (17, 23, 30), 'O': (148, 106, 66),
              'V': (12, 12, 20), 'P': (63, 184, 160), 'E': (199, 81, 75),
              'B': (156, 102, 196), 'D': (220, 179, 96), 'd': (220, 179, 96),
              'A': (110, 168, 221), 'a': (110, 168, 221)}

    def __init__(self, game):
        super().__init__(game)
        self.font = create_font(pixel_scale=1)
        self.title_font = create_font(pixel_scale=2)
        self.brush = '.'
        self.cursor = (9, 10)
        self.focus_name = False
        self.pending = None
        self.pending_kind = "discard"
        self.painting = False
        self.last_cell = None
        self.preview = None
        self.preview_image = None
        self.preview_full = False
        self.preview_dirty = True
        self.preview_wait = 0
        self.library_scroll = 0
        self.template_index = -1
        self.library = documents()
        self.buttons = []
        for index, (key, callback) in enumerate([
            ('new', lambda: self.guard(self.new_room)),
            ('save', self.save), ('copy', lambda: self.save(copy=True)),
            ('undo', self.undo), ('redo', self.redo), ('back', lambda: self.guard(self.close)),
        ]):
            self.buttons.append((pygame.Rect(169 + index * 77, 23, 73, 17), key, callback))
        self.new_room()

    def t(self, key):
        return self.game.localization.text('ui.room_editor.' + key)

    def new_room(self):
        self.rows = [list(row) for row in tower_room(['.' * 13] * 7 + ['..........P..'])]
        self.kind = 'normal'
        self.name = self.t('default_name')
        self.enabled = False
        self.path = None
        self.undo_stack = []
        self.redo_stack = []
        self.status = ''
        self.saved = self.state()
        self.preview_dirty = True

    def state(self):
        return (deepcopy(self.rows), self.name, self.kind, self.enabled)

    def restore(self, state):
        self.rows, self.name, self.kind, self.enabled = deepcopy(state)
        self.preview_dirty = True

    def remember(self):
        self.undo_stack.append(self.state())
        self.undo_stack = self.undo_stack[-80:]
        self.redo_stack.clear()
        self.status = ''

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.state())
            self.restore(self.undo_stack.pop())

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.state())
            self.restore(self.redo_stack.pop())

    def layout(self):
        return [''.join(row) for row in self.rows]

    def guard(self, callback):
        self.painting = False
        self.last_cell = None
        if self.state() != self.saved:
            self.pending_kind = "discard"
            self.pending = callback
        else:
            callback()

    def request_delete(self):
        if self.path is None:
            self.status = self.t('delete_select')
            return
        self.painting = False
        self.last_cell = None
        self.focus_name = False
        self.pending_kind = "delete"
        target = self.path
        saved_name = next((str(data.get('name', target.stem)) for path, data in self.library
                           if path == target), target.stem)
        self.delete_name = saved_name[:36]
        self.pending = lambda: self.delete_saved_room(target)

    def delete_saved_room(self, path):
        try:
            delete_room(path)
        except (OSError, ValueError):
            self.status = self.t('delete_error')
            return
        self.library = documents()
        self.library_scroll = min(self.library_scroll, max(0, len(self.library) - 6))
        self.new_room()
        self.status = self.t('deleted')

    def close(self):
        from game.screens.menu_screen import MenuScreen
        self.game.screen_manager.set_screen(MenuScreen(self.game))

    def save(self, copy=False):
        errors = validate(self.layout(), self.kind)
        if self.enabled and errors:
            self.status = self.t('cannot_activate')
            return
        try:
            self.path, _ = save_room(self.name, self.kind, self.layout(), self.enabled,
                                     None if copy else self.path)
            self.saved = self.state()
            self.library = documents()
            self.status = self.t('saved_active' if self.enabled else 'saved_draft')
        except (OSError, ValueError):
            self.status = self.t('save_error')

    def load(self, path, data):
        self.rows = [list(row) for row in data['layout']]
        self.name = str(data.get('name', path.stem))[:40]
        self.kind = data.get('type', 'normal')
        self.enabled = data.get('enabled', False) is True
        self.path = path
        self.saved = self.state()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.preview_dirty = True
        self.status = ''

    def template(self):
        templates = [(rows, 'normal') for rows in NORMAL_ROOMS] + [(rows, 'boss') for rows in BOSS_ROOMS]
        self.template_index = (self.template_index + 1) % len(templates)
        rows, kind = templates[self.template_index]
        self.remember()
        self.rows = [list(row) for row in rows]
        self.kind = kind
        self.preview_dirty = True

    def cell_at(self, pos):
        if not self.GRID.collidepoint(pos):
            return None
        return (int((pos[1] - self.GRID.y) // self.CELL), int((pos[0] - self.GRID.x) // self.CELL))

    def paint(self, cell, tile):
        if cell is None:
            return
        row, col = cell
        self.cursor = cell
        if not 2 <= row <= 9:
            self.status = self.t('locked')
            return
        if self.rows[row][col] == tile:
            return
        if tile in ('P', 'B'):
            for line in self.rows:
                for index, existing in enumerate(line):
                    if existing == tile:
                        line[index] = '.'
        self.rows[row][col] = tile
        self.preview_dirty = True

    def stroke(self, cell, tile):
        if cell is None:
            self.last_cell = None
            return
        if self.last_cell:
            r0, c0 = self.last_cell
            r1, c1 = cell
            steps = max(abs(r1-r0), abs(c1-c0))
            for i in range(steps + 1):
                self.paint((round(r0 + (r1-r0)*i/max(1,steps)), round(c0 + (c1-c0)*i/max(1,steps))), tile)
        else:
            self.paint(cell, tile)
        self.last_cell = cell

    def change_type(self):
        self.remember()
        self.kind = 'boss' if self.kind == 'normal' else 'normal'
        self.preview_dirty = True

    def handle_event(self, event):
        if self.preview_full:
            if (event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_v)) or event.type == pygame.MOUSEBUTTONDOWN:
                self.preview_full = False
            return
        if self.pending:
            if event.type == pygame.KEYDOWN and getattr(event, "repeat", False):
                return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                action = self.pending
                self.pending = None
                if event.key == pygame.K_RETURN:
                    action()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = self.screen_to_virtual(event.pos)
                if pygame.Rect(192, 183, 120, 22).collidepoint(pos):
                    action = self.pending
                    self.pending = None
                    action()
                elif pygame.Rect(324, 183, 120, 22).collidepoint(pos):
                    self.pending = None
            return
        if event.type == pygame.TEXTINPUT and self.focus_name:
            self.name = (self.name + ''.join(c for c in event.text if c.isprintable()))[:40]
            return
        if event.type == pygame.KEYDOWN:
            ctrl = event.mod & pygame.KMOD_CTRL
            if ctrl and event.key == pygame.K_s:
                self.save(copy=bool(event.mod & pygame.KMOD_SHIFT))
            elif ctrl and event.key == pygame.K_DELETE:
                self.request_delete()
            elif ctrl and event.key == pygame.K_z:
                self.redo() if event.mod & pygame.KMOD_SHIFT else self.undo()
            elif ctrl and event.key == pygame.K_y:
                self.redo()
            elif self.focus_name:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self.focus_name = False
                elif ctrl and event.key == pygame.K_a:
                    self.name = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]
            elif ctrl and event.key == pygame.K_n:
                self.guard(self.new_room)
            elif event.key == pygame.K_F2:
                self.remember()
                self.focus_name = True
            elif event.key == pygame.K_t:
                self.change_type()
            elif event.key == pygame.K_a:
                self.remember()
                self.enabled = not self.enabled
            elif event.key == pygame.K_F3:
                self.template()
            elif ctrl and event.key == pygame.K_o and self.library:
                paths = [path for path, _ in self.library]
                index = (paths.index(self.path) + 1) % len(paths) if self.path in paths else 0
                path,data = self.library[index]
                self.guard(lambda:self.load(path,data))
            elif event.key == pygame.K_ESCAPE:
                self.guard(self.close)
            elif event.key == pygame.K_v:
                self.preview_full = True
            elif pygame.K_1 <= event.key <= pygame.K_7:
                self.brush = self.TILES[event.key - pygame.K_1]
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                r, c = self.cursor
                self.cursor = (max(2,min(9,r+(event.key==pygame.K_DOWN)-(event.key==pygame.K_UP))),
                               max(0,min(12,c+(event.key==pygame.K_RIGHT)-(event.key==pygame.K_LEFT))))
            elif event.key in (pygame.K_SPACE, pygame.K_DELETE):
                self.remember()
                self.paint(self.cursor, ' ' if event.key == pygame.K_DELETE else self.brush)
            elif event.key == pygame.K_F12:
                self.game.toggle_fullscreen()
        elif event.type == pygame.MOUSEWHEEL:
            self.library_scroll = max(0,min(max(0,len(self.library)-6),self.library_scroll-event.y))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = self.screen_to_virtual(event.pos)
            self.focus_name = False
            if event.button == 1:
                if pygame.Rect(470, 61, 160, 90).collidepoint(pos):
                    self.preview_full = True
                    return
                if pygame.Rect(470, 277, 160, 18).collidepoint(pos):
                    self.request_delete()
                    return
                if pygame.Rect(10, 48, 148, 20).collidepoint(pos):
                    self.remember()
                    self.focus_name = True
                    return
                for rect, _, callback in self.buttons:
                    if rect.collidepoint(pos):
                        callback()
                        return
                for i, tile in enumerate(self.TILES):
                    if pygame.Rect(10, 102+i*22, 148, 19).collidepoint(pos):
                        self.brush = tile
                        return
                if pygame.Rect(10, 74, 72, 19).collidepoint(pos):
                    self.change_type()
                    return
                if pygame.Rect(86, 74, 72, 19).collidepoint(pos):
                    self.remember()
                    self.enabled = not self.enabled
                    return
                if pygame.Rect(10, 264, 148, 20).collidepoint(pos):
                    self.template()
                    return
                for index, (path, data) in enumerate(self.library[self.library_scroll:self.library_scroll+6]):
                    if pygame.Rect(470, 175+index*17, 160, 15).collidepoint(pos):
                        self.guard(lambda p=path,d=data:self.load(p,d))
                        return
            cell = self.cell_at(pos)
            if cell and event.button == 2:
                tile = self.rows[cell[0]][cell[1]]
                if tile in self.TILES:
                    self.brush = tile
            elif cell and event.button in (1,3):
                self.remember()
                self.painting = event.button
                self.last_cell = None
                self.stroke(cell, self.brush if event.button == 1 else ' ')
        elif event.type == pygame.MOUSEMOTION and self.painting:
            self.stroke(self.cell_at(self.screen_to_virtual(event.pos)), self.brush if self.painting == 1 else ' ')
        elif event.type == pygame.MOUSEBUTTONUP:
            self.painting = False
            self.last_cell = None

    def update(self, dt):
        self.preview_wait += dt
        if self.preview_dirty and (not self.painting or self.preview_wait > .2):
            self.preview_wait = 0
            self.preview_dirty = False
            state = random.getstate()
            try:
                random.seed(812)
                room = Room(self.layout(), self.kind, 640, 360)
                image = pygame.Surface((640,360))
                image.fill((13,19,25))
                room.draw(image)
                from game import config
                for r,line in enumerate(self.rows):
                    for c,tile in enumerate(line):
                        if tile in 'PEB':
                            center = (room.offset_x+(c+.5)*config.ROOM_CELL_SIZE,
                                      room.offset_y+(r+.5)*config.ROOM_CELL_SIZE)
                            pygame.draw.circle(image,self.COLORS[tile],center,7)
                            letter=self.font.render(tile,True,(255,255,255))
                            image.blit(letter,letter.get_rect(center=center))
                self.preview_image = image
                self.preview = pygame.transform.scale(image, (160,90))
            finally:
                random.setstate(state)

    def label(self, surface, text, pos, color=(230,235,222)):
        surface.blit(self.font.render(text, True, color), pos)

    def draw(self, surface):
        if self.preview_full and self.preview_image is not None:
            surface.blit(self.preview_image,(0,0))
            pygame.draw.rect(surface,(20,27,34),(145,339,350,15))
            self.label(surface,self.t('preview_back'),(153,344))
            return
        surface.fill((22,28,35))
        self.label(surface, self.t('title') + (' *' if self.state()!=self.saved else ''), (10,10), (236,211,143))
        for rect,key,_ in self.buttons:
            pygame.draw.rect(surface,(44,61,64),rect)
            image=self.font.render(self.t(key),True,(231,235,223))
            surface.blit(image,image.get_rect(center=rect.center))
        self.label(surface,self.t('name'),(10,38))
        pygame.draw.rect(surface,(63,80,78) if self.focus_name else (36,46,55),(10,48,148,20))
        self.label(surface,self.name[-35:] + ('_' if self.focus_name else ''),(14,55))
        for rect,text in [(pygame.Rect(10,74,72,19),self.t(self.kind)),(pygame.Rect(86,74,72,19),self.t('active' if self.enabled else 'draft'))]:
            pygame.draw.rect(surface,(44,61,64),rect)
            self.label(surface,text,(rect.x+5,rect.y+6))
        for i,tile in enumerate(self.TILES):
            rect=pygame.Rect(10,102+i*22,148,19)
            pygame.draw.rect(surface,(64,88,83) if tile==self.brush else (34,43,51),rect)
            pygame.draw.rect(surface,self.COLORS[tile],(14,rect.y+4,11,11))
            self.label(surface,f'{i+1}  '+self.t('tile_'+str(i)),(31,rect.y+6))
        pygame.draw.rect(surface,(44,61,64),(10,264,148,20))
        self.label(surface,self.t('template'),(17,271))
        for r,line in enumerate(self.rows):
            for c,tile in enumerate(line):
                rect=pygame.Rect(self.GRID.x+c*self.CELL,self.GRID.y+r*self.CELL,self.CELL,self.CELL)
                pygame.draw.rect(surface,self.COLORS.get(tile,(25,25,25)),rect)
                pygame.draw.rect(surface,(36,45,53),rect,1)
                if tile not in '. ':
                    self.label(surface,tile,(rect.centerx-2,rect.centery-2))
        r,c=self.cursor
        pygame.draw.rect(surface,(245,224,154),(self.GRID.x+c*self.CELL,self.GRID.y+r*self.CELL,self.CELL,self.CELL),2)
        self.label(surface,self.t('preview'),(470,48))
        if self.preview:
            surface.blit(self.preview,(470,61))
        self.label(surface,self.t('library')+f' ({len(self.library)})',(470,163))
        for i,(path,data) in enumerate(self.library[self.library_scroll:self.library_scroll+6]):
            rect=pygame.Rect(470,175+i*17,160,15)
            pygame.draw.rect(surface,(61,83,77) if path==self.path else (34,43,51),rect)
            self.label(surface,('+' if data.get('enabled') else '-')+' '+str(data.get('name',path.stem))[:36],(474,rect.y+5))
        pygame.draw.rect(surface,(99,48,48) if self.path else (36,43,49),(470,277,160,18))
        self.label(surface,self.t('delete_button'),(477,283), (238,216,203) if self.path else (115,123,128))
        errors=validate(self.layout(),self.kind)
        message=self.t('error_'+errors[0]) if errors else self.t('valid')
        self.label(surface,message,(10,300),(239,154,121) if errors else (157,214,167))
        self.label(surface,self.status,(10,310),(243,215,149))
        self.label(surface,self.t('help1'),(10,329))
        self.label(surface,self.t('help2'),(10,342))
        if self.pending:
            pygame.draw.rect(surface,(18,24,30),(173,140,294,77))
            pygame.draw.rect(surface,(227,199,134),(173,140,294,77),1)
            deleting = self.pending_kind == "delete"
            question = self.t('delete_question').format(name=self.delete_name) if deleting else self.t('discard_question')
            self.label(surface,question,(185,151))
            self.label(surface,self.t('delete_hint' if deleting else 'discard_hint'),(185,163))
            for rect,key in [(pygame.Rect(192,183,120,22),'delete_confirm' if deleting else 'discard'),(pygame.Rect(324,183,120,22),'keep')]:
                pygame.draw.rect(surface,(54,74,71),rect)
                self.label(surface,self.t(key),(rect.x+7,rect.y+8))
