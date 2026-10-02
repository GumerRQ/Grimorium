# Intro de Grimorium — primera versión animada

**Ya se puede ver y jugar.** Es un montaje de 20 segundos para comprobar la historia,
el ritmo y el chiste antes de dibujar más poses. Conserva el aspecto de los dibujos
originales y presenta al cuervo como una silueta fugaz, sin revelar al jefe final.

La resolución interna de la intro es **320 × 180 píxeles**. El juego y el vídeo
la amplían por múltiplos enteros, sin suavizar los píxeles. El MP4 de 1280 × 720
es una ampliación ×4 de esa imagen; no añade detalle.

## Verla

- [Vídeo con sonido, 1280 × 720, 24 fps](../../../output/intro/intro-v1.mp4).
- [Los momentos principales en una imagen](../../../output/intro/storyboard.png).
- Al abrir el juego aparece antes del menú. **Enter, Espacio o Esc** la saltan;
  **M** silencia el sonido y **F12** cambia la pantalla completa.
- Se puede repetir desde **Opciones → Ver intro**. Al terminar vuelve al menú.

No hace falta instalar un editor de vídeo ni aprender animación para ver esta versión.

## Qué cuenta

| Tiempo | Acción |
| --- | --- |
| 0–4,4 s | El mago camina distraído, leyendo. |
| 4,4–5,4 s | Una sombra lo cubre; él sigue a lo suyo. |
| 5,4–5,72 s | El cuervo pasa a toda velocidad y se lleva el libro. |
| 5,72–8,6 s | El mago sigue mirando el hueco, comprende lo ocurrido y sale corriendo. |
| 8,6–11,6 s | Vemos al ladrón perderse en la torre. |
| 11,6–17,5 s | El mago cruza la colina dando pequeños saltos y se acerca. |
| 17,5–20 s | Entra en la torre; aparece el título. |

La pausa después del robo sostiene el humor. El cuervo solo necesita una barriga,
un pico y masas grandes de alas para reconocerse durante la pasada. Su cara y el
diseño detallado se reservan para el jefe final.

## Qué está preparado

Se extrajeron las capas de `../intro.kra` en PNG transparentes con su posición
original. El archivo de Krita y los siete PNG originales no se modificaron.
`layers/manifest.json` guarda tamaños, posiciones y orden; las capas numéricas de
referencia se excluyen al reproducir la intro.

El movimiento se compone con desplazamientos, rebotes, giros, escalas y ocultación
tras la colina. Es animación de recortes: todavía no hay poses nuevas dibujadas
fotograma a fotograma. El mismo motor produce el vídeo y la intro del juego.

- `timeline.json`: duración y descripción de cada tramo.
- `layers/`: dibujos originales separados, listos para reutilizar.
- [crow-silhouette.png](crow-silhouette.png): recorte nuevo del cuervo, creado con
  ImageGen integrado. [Prompt exacto y procedencia](CROW-PROMPT.md).
- [intro-audio.wav](intro-audio.wav): música y efectos originales provisionales.
  [Detalles de audio y regeneración](AUDIO.md).
- `src/game/visuals/intro_sequence.py`, desde la raíz del proyecto: montaje visual.
- `src/game/screens/intro_screen.py`: reproducción y controles dentro del juego.

## Siguiente pasada artística

Esta versión sirve para decidir el ritmo viendo el resultado completo. Para darle
más actuación, las siguientes piezas útiles serían una pose mirando el libro que
ya no está, una pose de enfado cómico y dos posiciones sencillas de alas. No hace
falta redibujar los fondos ni revelar los ojos del cuervo. Esas poses se pueden
incorporar sobre el montaje que ya funciona.

## Herramientas de trabajo

Comandos desde la raíz del proyecto, usando el Python del juego con `pygame`:

```powershell
python tools/preview_intro.py
```

El visor permite **Espacio** para pausar, **R** para repetir, **M** para silenciar y
**Esc** para cerrar. Para sacar una versión nueva del vídeo se necesita también
FFmpeg en PATH o el paquete `imageio-ffmpeg`:

```powershell
python tools/preview_intro.py --export output/intro/intro-v2.mp4 --contact-sheet output/intro/storyboard-v2.png
```

Si se modifican los tiempos de `timeline.json`, también hay que reajustar los
eventos de `tools/build_intro_audio.py` y regenerar el audio para que coincidan.

Para volver a extraer las capas tras guardar cambios en Krita (requiere Pillow y
NumPy), conviene exportar primero a otra carpeta y revisar el resultado:

```powershell
python tools/extract_intro_layers.py assets/video/intro.kra output/intro/layers-revision
```

El extractor está preparado para las capas de pintura RGBA8 y los grupos
`Escena 1` a `Escena 7` de este documento. No es un importador general de Krita.

## Verificación de esta versión

Las 15 pruebas de la intro pasan: controles, audio opcional, regreso al menú,
repetición, dibujo de los recursos reales y reproducción al avanzar o retroceder
por los cortes. El MP4 se ha decodificado completo: 480 fotogramas y 20 segundos,
con pista de audio estéreo.

La batería general da 40 pruebas correctas y dos fallos ya presentes, reproducidos
también con `game.py` de HEAD: una prueba antigua usa `Game.max_cycles`, que ya no
existe, y otra espera opacidad en un píxel transparente de `combat_hud.png`.
