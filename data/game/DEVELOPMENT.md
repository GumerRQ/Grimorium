# Herramientas de desarrollo

## F9: panel

Disponible desde el menú principal y las salas de combate. La partida se pausa mientras está abierto. Usa arriba/abajo para seleccionar, izquierda/derecha para cambiar sala o enemigo, y Enter para aplicar. También admite ratón; las flechas de cada selector cambian su valor. F9 o Escape vuelve.

Permite cargar salas normales y de jefe (incluidas las personalizadas válidas), generar enemigos en espacios libres, ajustar vida actual/máxima y monedas, activar invulnerabilidad y vaciar la sala. Estas modificaciones se marcan como depuración en el historial de torre. Los cambios a la vida son temporales: no modifican config.py.

## Semillas

En F9, selecciona Editar semilla, pulsa Enter, Ctrl+A para vaciar el campo y escribe una semilla. Enter termina la edición. La opción Empezar partida con esta semilla reinicia la partida; Generar otra semilla solo prepara otro valor. Jugar desde el menú crea una semilla nueva.

La semilla se muestra en el panel y se guarda en el JSON del historial de torre. Con la misma versión del juego, datos, salas y decisiones de compra se repiten las salas, enemigos, destructibles y ofertas de tienda. Las partículas y la duración de los combates no alteran la generación del siguiente piso. Esto reproduce contenido, no una grabación exacta de movimientos o física. Cambiar datos o usar depuración puede cambiar el resultado.

## Enemigos: enemies.json

Los cuatro enemigos normales están definidos en `data/game/enemies.json`. `behavior` elige rat, goblin, golem o dragon. Puedes copiar una entrada con otra clave para añadir una variante sin programar. `enabled` y `weight` controlan su aparición; `health`, `health_growth`, `speed`, `damage`, `body_damage` y `radius` controlan sus valores. Vida por nivel: `int(health * health_growth ** (nivel - 1))`, mínimo 1.

`visual` contiene ruta, cuadrícula, tamaño y animaciones del sprite. `shooting` configura cadencia, velocidad/alcance de proyectiles y distancia preferida en comportamientos que disparan. Los valores JSON prevalecen para enemigos normales generados por la fábrica; los jefes mantienen sus comportamientos y estadísticas específicos en código.

## F5: recargar

Desde menú o combate abre el panel y recarga; dentro del panel también funciona F5. Recarga datos de enemigos/destructibles/tienda y el idioma actual; imágenes de enemigos, jugador, destructibles, corazones, paneles del HUD, paredes, puertas, suelo y paisaje. Limpia las cachés de efectos gráficos. Los PNG de efectos se validan antes de limpiar sus cachés.

Conserva posiciones, estado de puertas, objetos ya rotos y proporción de vida de los enemigos. No reinicia la sala. Las ofertas nuevas se aplican en la próxima tienda; los atributos ya comprados no se reaplican. Las salas personalizadas se leen al elegir/cargar salas y los efectos visuales ya materializados pueden conservar su imagen hasta terminar. El código Python y config.py requieren reiniciar el juego.

Si un archivo es inválido, el panel muestra el error y no aplica el lote. La recarga no modifica tus PNG ni los JSON editados. Los ajustes del HUD se guardan desde F8, no se sobrescriben al recargar.
