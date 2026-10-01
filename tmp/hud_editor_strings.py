import json
from pathlib import Path
es={
 'title':'EDITOR HUD - PARTIDA PAUSADA', 'save':'Guardar', 'done':'Guardar y salir', 'cancel':'Cancelar', 'undo':'Deshacer', 'reset':'Restablecer',
 'left':'Texto izquierda', 'center':'Texto centro', 'right':'Texto derecha', 'align_x':'Alinear columna', 'align_y':'Alinear fila',
 'distribute':'Igualar separacion vertical', 'all_stats':'Seleccionar estadisticas', 'saved':'Guardado', 'save_error':'No se pudo guardar. Reintenta o cancela.',
 'select':'Selecciona una zona de texto o un bloque.', 'help_mouse':'Arrastrar: mover | Shift+clic: seleccionar varios | Esquina: tamano',
 'help_keys':'Tab: siguiente | Flechas: 1px (+Shift: 10) | Ctrl+S: guardar | Ctrl+Z: deshacer | F8: listo | Esc: cancelar',
 'names':dict(zip(['health_bar','health_text','time','coins','damage','speed','fire_rate','shoot_distance','body_damage','tower_view','tower_title','floor_label','floor_value','loop_label','loop_value'],
 ['Barra de vida','Texto de vida','Tiempo','Monedas','Dano','Velocidad','Cadencia','Alcance','Dano de contacto','Vista de torre','Titulo de torre','Etiqueta de piso','Numero de piso','Etiqueta de tramo','Numero de tramo']))}
en={
 'title':'HUD EDITOR - GAME PAUSED', 'save':'Save', 'done':'Save and close', 'cancel':'Cancel', 'undo':'Undo', 'reset':'Reset',
 'left':'Text left', 'center':'Text center', 'right':'Text right', 'align_x':'Align column', 'align_y':'Align row',
 'distribute':'Distribute vertically', 'all_stats':'Select all stats', 'saved':'Saved', 'save_error':'Could not save. Retry or cancel.',
 'select':'Select a text zone or block.', 'help_mouse':'Drag: move | Shift+click: multi-select | Corner: resize',
 'help_keys':'Tab: next | Arrows: 1px (+Shift: 10) | Ctrl+S: save | Ctrl+Z: undo | F8: done | Esc: cancel',
 'names':dict(zip(es['names'],['Health bar','Health text','Time','Coins','Damage','Speed','Fire rate','Range','Contact damage','Tower view','Tower title','Floor label','Floor number','Loop label','Loop number']))}
for lang,strings in [('es',es),('en',en)]:
 p=Path('data/lang')/(lang+'.json');d=json.loads(p.read_text(encoding='utf-8'));d['ui']['hud_editor']=strings;p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
import ast
for p in Path('src').rglob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
print('Syntax OK.')
