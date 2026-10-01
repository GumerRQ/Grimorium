# Objetos destructibles - propuesta de sprites

Configuración del juego: `data/game/destructibles.json`. Ahí puedes cambiar las dimensiones de las casillas, resistencia, frecuencia, recompensa y colores de fondo por objeto; instrucciones en `data/game/DESTRUCTIBLES.md`. Las medidas y los tres golpes descritos abajo son los valores iniciales.

La hoja cenital `objetos-estados-cenital.png` está integrada. Los PNG editables del juego están en `assets/images/objects/destructibles/`, un archivo por tipo: `crate.png`, `barrel.png`, `open_box.png`, `stool.png`, `skull.png` y `bones.png`. Puedes retocarlos en Aseprite. La hoja original se conserva.

Filas de arriba abajo:
1. Caja cerrada de madera.
2. Barril.
3. Cajon abierto.
4. Taburete.
5. Calavera con huesos.
6. Monton de huesos.

Columnas de izquierda a derecha:
- Intacto: aspecto inicial y despues del primer impacto.
- Danado: aspecto despues del segundo impacto.
- Fragmentos: material para las particulas de rotura al tercer impacto.

Cada casilla O elige un tipo aleatorio al crear la sala. Tres impactos para romper: intacto con 0–1, dañado con 2, fragmentos con 3. Cuentan proyectiles del jugador, proyectiles enemigos y contacto de enemigos terrestres al avanzar. Los enemigos no los buscan: navegan hacia el jugador y pueden romper los que encuentran. Entre golpes de contacto hay 0,3 s; las balas cuentan individualmente. Al romperse dejan de bloquear y los fragmentos saltan, se dispersan y permanecen en el suelo. No dan monedas ni impiden completar la sala.

`prepare_tiles.py` permite volver a extraer los PNG desde la hoja cenital usando Pillow; ejecutarlo sobrescribe los PNG de estos objetos. No hace falta ejecutarlo para jugar. La lógica está en `src/game/rooms/destructible.py`.

Generado con la herramienta integrada de imagenes, usando los tiles actuales de pared y puerta como referencias. Se pidieron sprites de baja resolucion, paleta limitada, transparencia, estados alineados y fragmentos separados. Se realizo una segunda pasada para limpiar la transparencia exterior. Los fondos de las zonas vacias tienen alfa cero, aunque algunas vistas previas pueden mostrar su color RGB oculto.

## Formato editable del juego

Cada PNG es una fila de casillas de 32 x 32: intacto, dañado y un fragmento por casilla restante. Conserva la transparencia y la cuadrícula; puedes añadir fragmentos ampliando la imagen hacia la derecha en múltiplos de 32. Reinicia el juego para cargar los cambios.

Los antiguos PNG sueltos se conservan en `output/destructibles/individual_frames_backup/`; el juego ya no los utiliza. Las hojas actuales se han montado desde esos PNG, sin redibujar ni recolorear.

Se admite transparencia PNG y fondo RGB (90, 90, 90) en cualquiera de las hojas. Ese color exacto se vuelve transparente al cargar, también para calcular colisiones y recortar fragmentos. Los archivos originales no se modifican.

También se admite RGB (59, 90, 62), el fondo encontrado en el barril editado. Ambos colores se eliminan por coincidencia exacta al cargar.
