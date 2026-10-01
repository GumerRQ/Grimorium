# Partida, cierre de sala y acciones

`game.run_state` es el propietario del jugador (vida, monedas, inventario y efectos adquiridos), semilla, progreso, historial de torre y resultados de sala. Las pantallas consultan esta misma instancia. `Game` conserva ventana, pantallas y recursos de presentación; una partida nueva crea un `RunState` nuevo.

`RunState.advance`, `finish_step` y `floor_index` concentran las reglas de progresión. `purchase` comprueba disponibilidad y saldo antes de aplicar la compra. `grant_room_reward` calcula y acredita una recompensa una sola vez. Esto organiza el estado para futuros guardados; no añade aún guardar/continuar partidas ni serializa los objetos gráficos del jugador.

`RoomCompletion` coordina la secuencia `active -> cleared -> reward -> leaving`. Una muerte pasa a `dead` y tiene prioridad sobre completar la sala en el mismo fotograma. Abrir puertas, revelar la ampliación de la torre, calcular la recompensa y confirmar la salida tienen guardas contra repetición. El resultado vive en `RunState.rooms`, no en campos duplicados de la pantalla.

`Game.finish_current_screen(source)` solo acepta la pantalla actual y una transición por instancia. Los combates deben estar en `leaving`; las tiendas usan la misma entrada. La captura de la sala anterior, el avance y el cambio de pantalla siguen coordinados desde Game.

Teclado y ratón seleccionan una acción común: `activate_button` para menús/pausa/fin de partida, `ShopScreen.perform_action` para compras, libro de niveles y salida, y `RoomCompletion.confirm` para continuar tras la recompensa. Enter sigue saliendo de la tienda; E/Espacio activa el artículo seleccionado. No se duplican las reglas de compra por dispositivo.

La depuración usa `reopen_for_debug` cuando añade enemigos a una sala despejada y accede al mismo `run_state`. No se han cambiado los importes de recompensa ni las reglas de los artículos.
