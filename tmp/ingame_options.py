from pathlib import Path

def edit(name,old,new):
 p=Path(name);s=p.read_text(encoding='utf-8');assert old in s,(name,old);p.write_text(s.replace(old,new),encoding='utf-8')
base='src/game/'
edit(base+'screens/base_screen.py','    VIRTUAL_WIDTH = 320','    CAN_PAUSE = False\n    VIRTUAL_WIDTH = 320')
for file,cls in [('combat_screen','CombatScreen'),('shop_screen','ShopScreen'),('ascent_screen','AscentScreen')]:
 edit(base+f'screens/{file}.py',f'class {cls}(BaseScreen):',f'class {cls}(BaseScreen):\n    CAN_PAUSE = True')
edit(base+'core/screen_manager.py','\n\nclass ScreenManager:', '\nimport pygame\n\n\nclass ScreenManager:')
edit(base+'core/screen_manager.py','        if self.current_screen is not None:\n            self.current_screen.handle_event(event)', '''        if self.current_screen is not None:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if getattr(event, "repeat", False):
                    return
                if self.current_screen.CAN_PAUSE:
                    from game.screens.pause_screen import PauseScreen
                    self.set_screen(PauseScreen(self.current_screen.game, self.current_screen))
                    return
            self.current_screen.handle_event(event)''')
edit(base+'screens/combat_screen.py','''        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from game.screens.pause_screen import PauseScreen
            self.game.screen_manager.set_screen(PauseScreen(self.game, self))
            return
''','')
edit(base+'screens/ascent_screen.py','''    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from game.screens.pause_screen import PauseScreen
            self.game.screen_manager.set_screen(PauseScreen(self.game, self))

''','')
edit(base+'screens/shop_screen.py','''            elif event.key == pygame.K_ESCAPE:
                self.level_book_pinned = False
                self.focus_index = len(self.keyboard_targets()) - 1
''','')
edit(base+'screens/menu_screen.py','def __init__(self, game):','def __init__(self, game, return_screen=None):')
edit(base+'screens/menu_screen.py','        super().__init__(game)','        super().__init__(game)\n        self.return_screen = return_screen')
edit(base+'screens/menu_screen.py',"        self.open_page('main')","        self.open_page('options' if return_screen is not None else 'main')")
edit(base+'screens/menu_screen.py',"lambda: self.open_page('main', 1), self.game.localization.text(\"ui.menu.back_desc\")", "self.back_from_options, self.game.localization.text('ui.pause.back_desc' if self.return_screen is not None else 'ui.menu.back_desc')")
edit(base+'screens/menu_screen.py','    def quit_game(self):','''    def back_from_options(self):
        if self.return_screen is not None:
            self.game.screen_manager.set_screen(self.return_screen)
        else:
            self.open_page('main', 1)

    def quit_game(self):''')
edit(base+'screens/menu_screen.py',"                self.open_page('main', 0 if self.page == 'main' else 1)","                if self.return_screen is not None:\n                    self.back_from_options()\n                else:\n                    self.open_page('main', 0 if self.page == 'main' else 1)")
p=Path(base+'screens/pause_screen.py');s=p.read_text(encoding='utf-8')
s=s.replace('class PauseScreen(BaseScreen):','class PauseScreen(BaseScreen):\n    VIRTUAL_WIDTH = 640\n    VIRTUAL_HEIGHT = 360')
s=s.replace('        self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT = previous_screen.get_virtual_size()\n','')
start=s.index('        center_x =');end=s.index('        self.overlay =',start)
s=s[:start]+'''        frozen = pygame.Surface(previous_screen.get_virtual_size())
        previous_screen.draw(frozen)
        self.frozen = pygame.transform.scale(frozen, self.get_virtual_size())
        self.title_font = create_font(15)
        self.selected = 0
        self.buttons = []
        self.on_enter()

'''+s[end:]
start=s.index('    def _resume(self):')
s=s[:start]+'''    def on_enter(self):
        t = self.game.localization.text
        actions = [(t("ui.pause.resume"), self._resume),
                   (t("ui.menu.options"), self._options),
                   (t("ui.pause.menu"), self._go_menu)]
        self.buttons = [Button((220, 140 + index * 40, 200, 30), label, callback,
                               font_size=14)
                        for index, (label, callback) in enumerate(actions)]

    def _options(self):
        from game.screens.menu_screen import MenuScreen
        self.game.screen_manager.set_screen(MenuScreen(self.game, return_screen=self))

'''+s[start:]
s=s.replace('self.previous_screen.draw(surface)','surface.blit(self.frozen, (0, 0))').replace('self.VIRTUAL_HEIGHT // 2 - 45','110')
s=s.replace('''            if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s, pygame.K_TAB):
                self.selected = (self.selected + 1) % len(self.buttons)''','''            if event.key == pygame.K_F12:
                self.game.toggle_fullscreen()
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s, pygame.K_TAB):
                backwards = event.key in (pygame.K_UP, pygame.K_w) or (
                    event.key == pygame.K_TAB and event.mod & pygame.KMOD_SHIFT)
                self.selected = (self.selected + (-1 if backwards else 1)) % len(self.buttons)''')
p.write_text(s,encoding='utf-8')
# Refresh only translated shop art when returning from pause, retaining inventory and selection.
p=Path(base+'screens/shop_screen.py');s=p.read_text(encoding='utf-8')
a=s.index('        # Replace lettering');b=s.index('        self.tooltip_icon_w',a)
labels=s[a:b];s=s[:a]+'        self.unlabeled_background = self.background.copy()\n'+s[b:]
a=s.index('        page_color =');b=s.index('        # Libro centrado',a)
book=s[a:b];s=s[:a]+'''        self.unlabeled_book = power_levels_book_original.copy()
        self.refresh_language()

'''+s[b:]
a=s.index('    def ',s.index('    def __init__')+10)
methods='''    def on_enter(self):
        if self.art_language != self.game.localization.language:
            self.refresh_language()

    def refresh_language(self):
        self.art_language = self.game.localization.language
        self.background = self.unlabeled_background.copy()
'''+labels+'''        power_levels_book_original = self.unlabeled_book.copy()
'''+book+'\n'
s=s[:a]+methods+s[a:]
s=s.replace('self.notice, self.notice_time = self.game.localization.text("ui.shop.poor")','self.notice, self.notice_time = "ui.shop.poor"').replace('self.notice, self.notice_time = self.game.localization.text("ui.shop.bought")','self.notice, self.notice_time = "ui.shop.bought"')
s=s.replace('hint = self.notice if self.notice_time > 0','hint = self.game.localization.text(self.notice) if self.notice_time > 0')
p.write_text(s,encoding='utf-8')
import json
for lang,text in [('es','Vuelve a la pausa.\nLa partida sigue detenida.'),('en','Return to the pause menu.\nYour run remains paused.')]:
 p=Path('data/lang')/(lang+'.json');d=json.loads(p.read_text(encoding='utf-8'));d['ui']['pause']['back_desc']=text;p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Pause and in-game options connected.')
