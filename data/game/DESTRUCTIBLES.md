# Objetos destructibles

Edita `destructibles.json` y reinicia el juego. Cada clave identifica un tipo; para añadir otro, copia una entrada y cambia su `asset`. Las casillas O de las salas eligen entre los tipos activos.

| Campo | Uso |
|---|---|
| `enabled` | Activa o desactiva el tipo. |
| `asset` | Ruta del PNG dentro de assets. |
| `frame_size` | Ancho y alto de cada casilla del PNG. No escala el dibujo. |
| `hits_to_break` | Impactos necesarios para romperse, independientemente del daño de la bala. |
| `damaged_after_hits` | Número de impactos a partir del que muestra el estado dañado. |
| `weight` | Peso relativo al elegir el objeto. 2 aparece el doble que 1; 0 no aparece. |
| `body_hit_interval` | Segundos mínimos entre impactos por contacto de enemigos. |
| `coins` | Monedas que se suman al jugador al romperse, también si lo rompe un enemigo. |
| `background_colors` | Colores RGB exactos que se convierten en transparentes. |

El PNG sigue siendo una sola fila: intacto, dañado y un fragmento por casilla restante. Puede haber casillas de fragmentos vacías. Los valores iniciales conservan tres impactos, estado dañado al segundo, igual frecuencia y ninguna moneda.

Para cambiar únicamente colores o formas, edita el PNG; no necesitas cambiar el JSON.
