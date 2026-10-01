import json,ast
from pathlib import Path
pairs={
 'title':('EDITOR DE SALAS - 13 x 11','ROOM EDITOR - 13 x 11'),
 'default_name':('Sala nueva','New room'), 'new':('Nueva','New'), 'save':('Guardar','Save'), 'copy':('Guardar copia','Save copy'), 'undo':('Deshacer','Undo'), 'redo':('Rehacer','Redo'), 'back':('Volver','Back'),
 'name':('Nombre (clic para editar)','Name (click to edit)'), 'normal':('Normal','Normal'), 'boss':('Jefe','Boss'), 'active':('Activa','Active'), 'draft':('Borrador','Draft'),
 'tile_0':('Suelo','Floor'), 'tile_1':('Vacio / pared','Void / wall'), 'tile_2':('Obstaculo','Obstacle'), 'tile_3':('Foso','Pit'), 'tile_4':('Jugador','Player'), 'tile_5':('Enemigo','Enemy'), 'tile_6':('Jefe','Boss'),
 'template':('Cargar siguiente plantilla','Load next template'), 'preview':('Vista previa real','Actual art preview'), 'library':('Salas guardadas (rueda)','Saved rooms (scroll)'),
 'locked':('Puertas y borde bloqueados para encajar en la torre.','Doors and outer rows are fixed to fit the tower.'),
 'valid':('Sala valida. Puedes activarla para las partidas.','Valid room. You can activate it for runs.'),
 'cannot_activate':('Corrige los errores o cambia a Borrador para guardar.','Fix the errors or switch to Draft to save.'),
 'saved_active':('Guardada: ya puede aparecer en las partidas.','Saved: this room can now appear in runs.'),
 'saved_draft':('Borrador guardado: no aparece en las partidas.','Draft saved: it will not appear in runs.'),
 'save_error':('No se pudo guardar la sala.','Could not save the room.'),
 'error_size':('La sala debe tener 13 columnas y 11 filas.','The room must have 13 columns and 11 rows.'),
 'error_type':('Tipo de sala no valido.','Invalid room type.'), 'error_doors':('La entrada y salida deben mantener su posicion.','Entrance and exit must keep their positions.'),
 'error_tiles':('La sala contiene casillas no reconocidas.','The room contains unsupported tiles.'),
 'error_player':('Coloca exactamente un punto de jugador.','Place exactly one player spawn.'),
 'error_boss':('Sala de jefe: un jefe. Sala normal: ningun jefe.','Boss room: one boss. Normal room: no bosses.'),
 'error_access':('Deja suelo libre delante de ambas mitades de cada puerta.','Leave walkable floor in front of both halves of each door.'),
 'error_disconnected':('Hay suelo o enemigos aislados: conecta las zonas.','Some floor or enemies are isolated: connect the areas.'),
 'help1':('Clic/arrastrar: pintar | Derecho: borrar | Central: cuentagotas | 1-7: pincel','Click/drag: paint | Right: erase | Middle: eyedropper | 1-7: brush'),
 'help2':('Flechas + Espacio: pintar | Ctrl+S: guardar | Ctrl+Z/Y: deshacer/rehacer | Esc: volver','Arrows + Space: paint | Ctrl+S: save | Ctrl+Z/Y: undo/redo | Esc: back'),
 'discard_question':('Hay cambios sin guardar. Descartarlos?','There are unsaved changes. Discard them?'),
 'discard_hint':('Enter: descartar | Escape: seguir editando','Enter: discard | Escape: keep editing'),
 'discard':('Descartar','Discard'), 'keep':('Seguir editando','Keep editing')}
hud={
 'redo':('Rehacer','Redo'), 'invalid_number':('Valor no valido o fuera de la pantalla.','Invalid value or outside the screen.'),
 'preview_hint':('Vista limpia - H: volver','Clean preview - H: return'), 'grid':('Rejilla','Grid'),
 'help_mouse':('G: modo | Alt+clic: superpuestos | Shift+clic: varios | Shift+esquina: proporcion | H: vista limpia','G: mode | Alt+click: overlapping | Shift+click: multi-select | Shift+corner: aspect ratio | H: preview'),
 'help_keys':('Ctrl+O: PNG | R: recargar | Ctrl+G: vincular | Ctrl+S: guardar | Ctrl+Z/Y: deshacer/rehacer | F8: listo','Ctrl+O: PNG | R: reload | Ctrl+G: link | Ctrl+S: save | Ctrl+Z/Y: undo/redo | F8: done')}
for index,lang in enumerate(('es','en')):
 p=Path('data/lang')/(lang+'.json');d=json.loads(p.read_text(encoding='utf-8'))
 d['ui']['room_editor']={k:v[index] for k,v in pairs.items()}
 d['ui']['hud_editor'].update({k:v[index] for k,v in hud.items()})
 d['ui']['menu']['room_editor']=('Crear salas','Room editor')[index]
 d['ui']['menu']['room_editor_desc']=('Dibuja salas sobre casillas.\nGuarda, revisa y activa tus\ncreaciones para las partidas.','Paint rooms on a grid.\nSave, preview and activate\nyour creations for runs.')[index]
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for p in Path('src').rglob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
print('Editor syntax and localization files ready.')
