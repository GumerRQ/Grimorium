# Paisaje de la torre

Los PNG de esta carpeta son los archivos que carga el juego. Se pueden abrir y
modificar directamente en **Aseprite, LibreSprite o Krita**. No hace falta generar
un dibujo por piso ni instalar herramientas nuevas para jugar.

| PNG | Tamaño | Uso |
| --- | --- | --- |
| `ground_moss.png` | 64 × 64 | Suelo opaco repetible |
| `tree_oak.png` | 56 × 56 | Copa de roble, transparente |
| `tree_pine.png` | 48 × 48 | Conífera vista desde arriba, transparente |
| `tree_birch.png` | 44 × 44 | Copa pequeña, transparente |
| `rock_large.png` | 24 × 20 | Roca con musgo, transparente |
| `rock_small.png` | 18 × 16 | Piedras pequeñas, transparente |
| `cloud_wide.png` | 112 × 56 | Banco de nubes alargado, transparente |
| `cloud_round.png` | 80 × 60 | Banco compacto, transparente |
| `combat_hud.png` | 640 × 360 | HUD existente con exterior transparente |

`preview.png` reúne los ocho elementos nuevos. `source/` conserva los originales
de alta resolución generados con la herramienta integrada **image_gen** y el
conjunto exacto de instrucciones en `source/prompts.json`.

## Editar el arte

1. Abre el PNG de esta carpeta en Aseprite y edítalo con el lápiz a tamaño de píxel.
2. Guarda con el mismo nombre, tamaño y transparencia. Si necesitas capas, guarda
   además tu copia `.aseprite` y exporta el PNG con ese mismo nombre.
3. Reinicia la partida para recargar los recursos. En la vista de prueba basta R.

La transparencia debe ser real, no un tablero de cuadros pintado. Las sombras y
luces forman parte del dibujo; la bruma y el movimiento se calculan en el juego.
El HUD original (`assets/images/combat_screen.png`) sigue conservado.

## Probar sin recorrer todos los pisos

Desde la raíz del proyecto, con el mismo Python que usas para jugar:

```powershell
python tools/preview_tower.py
```

Flechas o espacio para cambiar de altura, Inicio/Fin para ir a los extremos,
R para recargar los PNG y Escape para salir. Se usa una sala real sin enemigos.
También puedes exportar capturas con `--headless --output tmp/tower-preview`.

## Ajustes

En `src/game/config.py`:

- `TOWER_ASCENT_SECONDS`: duración de la transición (4,5 segundos).
- `TOWER_ZOOM_PER_FLOOR`: cuánto se aleja el terreno (0,07).
- `TOWER_MIN_GROUND_SCALE`: límite de reducción (0,32).
- `TOWER_CLOUD_SPEED`: velocidad del viento (1,5).
- `TOWER_LANDSCAPE_SEED`: cambia la distribución del bosque.

La altura cuenta solo los combates normales y los jefes, se acumula entre loops y
se conserva en las tiendas. El paisaje solo avanza su animación al actualizar una
sala de combate; dibujarlo durante una pausa no mueve las nubes. Una partida nueva
o una prueba de jefe reinicia la altura. El recorrido actual tiene 18 pisos.

El terreno se compone una vez por partida con una semilla local, sin consumir la
aleatoriedad de enemigos/salas. Solo se recalcula su encuadre cuando cambia el
zoom o la bruma, y las variantes de sprites tienen una caché limitada.

## Reimportar originales (opcional)

`node tools/prepare_tower_assets.cjs` requiere el módulo de desarrollo `sharp`.
Recorta el margen transparente de los originales, exporta a tamaño de juego con
vecino más próximo y paleta reducida, separa el HUD y crea la lámina de recursos.
**Sobrescribe los PNG de esta carpeta**: no lo ejecutes sobre ediciones manuales
que no hayas guardado aparte. El juego no necesita Node ni sharp.
