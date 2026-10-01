import ast, io, json, tokenize
from pathlib import Path
root=Path.cwd()
translations={}
def localize(file, group, entries, accessor='self.game.localization.text'):
    p=root/file
    source=p.read_text(encoding='utf-8')
    replacements={}
    for key, es, en in entries:
        translations.setdefault(group,{})[key]=(es,en)
        replacements[es]=f'{accessor}("ui.{group}.{key}")'
    offsets=[0]
    for line in source.splitlines(keepends=True): offsets.append(offsets[-1]+len(line))
    edits=[]
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type==tokenize.STRING:
            try: value=ast.literal_eval(tok.string)
            except (ValueError,SyntaxError): continue
            if value in replacements:
                edits.append((offsets[tok.start[0]-1]+tok.start[1],offsets[tok.end[0]-1]+tok.end[1],replacements[value]))
    for start,end,new in reversed(edits): source=source[:start]+new+source[end:]
    p.write_text(source,encoding='utf-8')
def change(file,old,new):
    p=root/file;s=p.read_text(encoding='utf-8');assert old in s,(file,old);p.write_text(s.replace(old,new),encoding='utf-8')
localize('src/game/screens/menu_screen.py','menu',[
('play','Jugar','Play'),('options','Opciones','Options'),('controls','Controles','Controls'),('practice','Practicar jefes','Boss practice'),('quit','Salir','Quit'),('back','Volver','Back'),
('play_desc','Empieza una nueva partida.\nSube pisos, mejora tu equipo\ny descubre hasta donde llegas.','Start a new run.\nClimb floors, upgrade gear\nand see how far you can go.'),
('options_desc','Ajusta la pantalla y el\ncontador de rendimiento.','Choose your language, display\nand performance counter.'),
('controls_desc','Consulta como moverte,\ndisparar y cambiar de arma.','Learn how to move, shoot\nand switch weapons.'),
('practice_desc','Entra directamente en un\ncombate para practicar.','Jump into a boss fight\nto practice.'),('quit_desc','Cierra el juego.','Close the game.'),
('display','Pantalla: ','Display: '),('fullscreen','completa','full'),('window','ventana','window'),('fps','Mostrar FPS: ','Show FPS: '),('yes','Si','Yes'),('no','No','No'),
('display_desc','Alterna ventana y pantalla\ncompleta. Atajo: F12.','Switch between windowed\nand fullscreen. Shortcut: F12.'),
('fps_desc','Muestra u oculta el contador\nde FPS y tiempo por fotograma.','Show or hide FPS\nand frame time.'),('back_desc','Vuelve al menu principal.','Return to the main menu.'),
('golem','Golem saltador','Leaping golem'),('basic','Jefe basico','Basic boss'),('golem_desc','Practica los saltos y ataques\ndel golem.','Practice against the\ngolem and its jumping attacks.'),('basic_desc','Combate de prueba contra\nel jefe basico.','Practice against\nthe basic boss.'),
('heading_main','CADA PISO CUENTA','EVERY FLOOR COUNTS'),('heading_options','OPCIONES','OPTIONS'),('heading_controls','CONTROLES','CONTROLS'),('heading_practice','PRACTICAR JEFES','BOSS PRACTICE'),
('how','COMO JUGAR','HOW TO PLAY'),('move','Moverte','Move'),('arrows','Flechas','Arrows'),('shoot','Disparar','Shoot'),('weapon','Cambiar arma','Switch weapon'),('shop','Salir / equipar','Leave / equip'),('pause','Pausar / volver','Pause / back'),('full_control','Pantalla completa','Fullscreen'),('next','TU SIGUIENTE PASO','YOUR NEXT STEP'),
('session','Cambios para esta sesion.','Language saved automatically.'),('footer','Raton: elegir   Flechas: navegar   Enter: aceptar   Esc: volver','Mouse: select   Arrows: navigate   Enter: confirm   Esc: back')])
# Use accurate text for the persisted language setting; other options remain session-only.
translations['menu']['session']=('El idioma se guarda.','Language saved automatically.')
translations['menu']['options_desc']=('Ajusta el idioma, la pantalla\ny el contador de rendimiento.',translations['menu']['options_desc'][1])
translations['menu']['language']=('Idioma: Castellano','Language: English')
translations['menu']['language_desc']=('Castellano / English\nSe guarda para la próxima vez.','Castellano / English\nRemembered for the next launch.')
translations['menu']['save_failed']=('No se pudo guardar el idioma.','Could not save the language.')
change('src/game/screens/menu_screen.py',"        self.page = 'main'","        self.language_saved = True\n        self.page = 'main'")
change('src/game/screens/menu_screen.py',"        elif page == 'options':\n            entries = [","        elif page == 'options':\n            entries = [\n                (self.game.localization.text('ui.menu.language'), self.toggle_language,\n                 self.game.localization.text('ui.menu.language_desc')),")
change('src/game/screens/menu_screen.py','    def toggle_fps(self):','    def toggle_language(self):\n        language = "en" if self.game.localization.language == "es" else "es"\n        self.language_saved = self.game.localization.set_language(language)\n        self.open_page("options", self.selected)\n\n    def toggle_fps(self):')
change('src/game/screens/menu_screen.py','self.game.localization.text("ui.menu.session")','self.game.localization.text("ui.menu.session" if self.language_saved else "ui.menu.save_failed")')
change('src/game/core/game.py','Localization("en")','Localization()')
localize('src/game/screens/pause_screen.py','pause',[('resume','Continuar','Resume'),('menu','Menu','Menu'),('title','Pausa','Paused')])
localize('src/game/screens/game_over_screen.py','end',[('again','Jugar otra vez','Play again'),('menu','Menu','Menu'),('win','Tower complete','Tower complete'),('lose','Game Over','Game over'),('hint','Flechas: elegir | Enter: aceptar | Escape: menu','Arrows: select | Enter: confirm | Escape: menu'),('tower','TU TORRE','YOUR TOWER')])
translations['end']['win']=('Torre completada','Tower complete');translations['end']['lose']=('Fin de la partida','Game over')
translations['end']['score']=('Puntos: {score}','Score: {score}');translations['end']['floors']=('{count} pisos visitados','{count} floors visited')
change('src/game/screens/game_over_screen.py','f"Puntos: {self.final_score}"','self.game.localization.text("ui.end.score").format(score=self.final_score)')
change('src/game/screens/game_over_screen.py','f"{len(self.history.floors)} pisos visitados"','self.game.localization.text("ui.end.floors").format(count=len(self.history.floors))')
localize('src/game/screens/shop_screen.py','shop',[('poor','No tienes monedas suficientes','Not enough coins'),('bought','Comprado','Purchased'),('levels','I  Niveles','I  Levels'),('leave','Enter  Salir','Enter  Leave'),('hint','E: equipar  Shift: detalle','E: equip  Shift: details')])
translations['shop']['level']=('nv:','lv:')
change('src/game/screens/shop_screen.py','f"lv:', 'self.game.localization.text("ui.shop.level") + f"')
localize('src/game/ui/room_reward_card.py','reward',[('title','SALA COMPLETADA','ROOM CLEARED'),('subtitle','RECOMPENSA DE LA SALA','ROOM REWARD'),('health','Vida restante','Health remaining'),('time','Tiempo de sala','Room time'),('savings','Ahorro','Savings'),('savings_detail','1 por cada 15 monedas, maximo 3','1 per 15 coins, up to 3'),('continue','Enter / Continuar','Enter / Continue')], 'self.localization.text')
change('src/game/ui/room_reward_card.py','def __init__(self, reward):','def __init__(self, reward, localization):\n        self.localization = localization')
translations['reward']['health_detail']=('{life:g} de vida / 2','{life:g} health / 2');translations['reward']['time_detail']=('{seconds:.1f}s | 5 monedas menos 1 cada 5s','{seconds:.1f}s | 5 coins minus 1 per 5s')
change('src/game/ui/room_reward_card.py','f"{r[\'life\']:g} de vida / 2"','self.localization.text("ui.reward.health_detail").format(**r)')
change('src/game/ui/room_reward_card.py','f"{r[\'seconds\']:.1f}s | 5 monedas menos 1 cada 5s"','self.localization.text("ui.reward.time_detail").format(**r)')
change('src/game/screens/combat_screen.py','RoomRewardCard(self.room_reward)','RoomRewardCard(self.room_reward, self.game.localization)')
translations['combat']={'time':('Tiempo: {seconds:.1f}','Time: {seconds:.1f}')}
change('src/game/screens/combat_screen.py','f"Time: {self.room_time:.1f}"','self.game.localization.text("ui.combat.time").format(seconds=self.room_time)')
localize('src/game/visuals/tower_track.py','tower',[('title','TORRE','TOWER'),('floor','PISO','FLOOR'),('loop','TRAMO','LOOP'),('top','CIMA','TOP')], 'localization.text')
change('src/game/visuals/tower_track.py','def draw(self, surface, history, font, current_floor):','def draw(self, surface, history, font, current_floor, localization):')
change('src/game/screens/combat_screen.py','self.game.get_tower_floor_index())','self.game.get_tower_floor_index(), self.game.localization)')
for language,index in [('es',0),('en',1)]:
    p=root/'data/lang'/f'{language}.json';data=json.loads(p.read_text(encoding='utf-8'))
    for group,entries in translations.items():data['ui'][group]={key:pair[index] for key,pair in entries.items()}
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Localized menu, shop, combat, tower, pause, end screen and rewards.')
