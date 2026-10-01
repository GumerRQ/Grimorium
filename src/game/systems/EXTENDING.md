# Añadir contenido y mecánicas

## Impactos

Las fuentes de daño llaman a `apply_impact(target, Impact(...))` de `impacts.py` después de detectar la colisión. `damage`, `kind`, `source`, `knockback` y `strength` describen el impacto. El resultado indica si se aceptó y si el objetivo murió. `execute=True` está reservado para ejecuciones que ignoran la cantidad de daño.

Los seres vivos mantienen en `take_damage` sus reglas de invulnerabilidad, veneno y sentencia. Los destructibles implementan `receive_impact`: cuentan un golpe y aplican su intervalo de contacto; al romperse notifican a la sala para liberar la colisión, crear los fragmentos y acreditar la recompensa. Para recorrer destructibles que pueden desaparecer durante un ataque de área, usa una copia: `tuple(room.destructibles)`.

No añadas llamadas directas a `take_damage` desde nuevas balas o efectos. Un ataque de área detecta sus objetivos y envía a cada uno un `Impact(kind="effect", ...)`. No se han cambiado los objetivos de los efectos existentes.

## Efectos

`CombatEffects` posee las colecciones, las interacciones elementales y el dibujo por capas. `CombatScreen` coordina las fases y entrega los efectos nuevos con `effects.add_all(...)`.

Un efecto normal implementa `update(dt, enemies)`, `draw(surface)` y `finished`. `update` puede devolver una lista de efectos o balas nuevos. Se añade con `effects.add(effect)` sin modificar la pantalla de combate. Los efectos especiales que necesitan otra firma o una capa inferior se registran en `CombatEffects.routes` y se coordinan dentro del gestor, como el hielo y las nubes existentes. El orden de fases previo se conserva.

## HUD

El formato de layout es versión 3. Un panel con `fit_to: "health_bar"` ajusta su ancho a los corazones y figura como su contenedor en `members`; el nombre de la imagen no decide su comportamiento. Las versiones 1 y 2 se migran al cargar.

En F8 selecciona el PNG y los corazones con Shift y pulsa Vincular/Ctrl+G. El vínculo ajusta el ancho y permite mover ambos juntos. Vincular ese panel sin los corazones retira el ajuste automático. Borrar, deshacer y guardar conservan estas propiedades. El PNG puede llamarse como quieras.
