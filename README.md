# Grimorium

Grimorium es un juego hecho en Python con `pygame`.

El proyecto está en desarrollo y la idea es ir construyéndolo poco a poco mientras pruebo mecánicas, combate, salas, tienda y progresión.

## Cómo jugar

Si solo quieres probar el juego, ve a la sección de **Releases** del repositorio, descarga la última versión en `.zip`, descomprímela y ejecuta `Grimorium.exe`.

## Desarrollo

### Requisitos
- Python 3
- `pygame`

### Ejecutarlo en local
```bash
py -m pip install -r requirements.txt
py run_game.py
```

### Estructura
- src/: código principal del juego
- assets/: imágenes y recursos visuales
- data/: datos auxiliares del proyecto


### Estado del proyecto
Proyecto en desarrollo. Puede haber cambios frecuentes, errores y contenido provisional.

### Autor
AlbertoRQ

### Editor visual del HUD de combate
Pulsa **F8** dentro de una sala. La partida se congela mientras editas.

- Arrastra las zonas para mover los numeros, la barra de vida o la vista de la torre.
- Shift + clic selecciona varios elementos; Tab permite recorrerlos, incluso si se superponen.
- Arrastra la esquina inferior derecha de una zona seleccionada para cambiar su tamano.
- Los botones permiten alinear el texto, alinear grupos y repartir las filas verticalmente.
- Flechas mueven 1 pixel logico; Shift + flechas mueven 10.
- Ctrl + Z deshace. Ctrl + S guarda sin cerrar. F8 guarda y vuelve a la partida.
- Escape o Cancelar descartan los cambios desde el ultimo guardado y vuelven a la partida.

Las posiciones se guardan en `data/hud_layout.json` al ejecutar desde el proyecto; en el ejecutable, en `%APPDATA%/Grimorium/hud_layout.json`. Se aplican a todas las salas y se cargan en el siguiente arranque. El editor recoloca las zonas del HUD; no modifica los dibujos de los PNG.

El editor tambien permite mover los graficos: **G** alterna Todo / Graficos / Contenido. Los paneles izquierdo y de torre estan separados en `assets/images/hud/panels/` y arrastrarlos mueve su contenido asociado. **Anadir PNG** (Ctrl+O) incorpora nuevos paneles; **Vincular** (Ctrl+G) asocia las zonas seleccionadas a un panel. **R** recarga los PNG retocados sin reiniciar. El antiguo `combat_hud.png` se conserva como referencia y ya no se dibuja. Detalles en `assets/images/hud/panels/README.md`.

### Mejoras de los editores

HUD (F8): campos X/Y/W/H editables con Enter para aplicar, rejilla de ajuste de 1/4/8 pixeles, Ctrl+Y o Ctrl+Shift+Z para rehacer, Alt+clic para seleccionar elementos superpuestos, Shift al redimensionar para conservar proporciones y H para alternar una vista limpia. Las coordenadas se expresan en pixeles logicos de 640 x 360.

Salas: **Menu > Crear salas** permite pintar la cuadricula y ver una previsualizacion con los recursos del juego. Las salas guardadas como Activas se incorporan automaticamente a las partidas; los Borradores quedan fuera. Documentacion y controles en `data/levels/README.md`.
