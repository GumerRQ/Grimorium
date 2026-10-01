# Editor de salas

Entra desde el menu principal: **Crear salas**.

La cuadricula conserva las 13 columnas y 11 filas de la torre. Las ocho filas interiores se pintan; las puertas dobles y filas exteriores se mantienen alineadas. El motor crea automaticamente las paredes alrededor del suelo. No necesitas dibujar paredes ni escribir los mapas en Python.

- Clic o arrastrar: pintar; boton derecho: vacio; boton central: copiar pincel.
- 1-7: suelo, vacio/pared, obstaculo, foso, jugador, enemigo y jefe.
- Flechas y Espacio: mover cursor y pintar usando teclado; Supr: borrar casilla.
- Nombre: clic o F2; Ctrl+A vacia el nombre mientras lo editas.
- T cambia Normal/Jefe; A cambia Borrador/Activa.
- F3 carga la siguiente plantilla del juego; puedes modificarla sin alterar la original.
- V o clic sobre la miniatura abre una vista ampliada con los graficos reales. Los puntos P/E/B indican apariciones, no una simulacion de combate.
- Ctrl+Z / Ctrl+Y: deshacer / rehacer por pincelada.
- Ctrl+S: guardar; Ctrl+Shift+S: guardar copia; Ctrl+N: nueva.
- La lista de la derecha abre salas guardadas; la rueda desplaza la lista. Ctrl+O recorre las salas guardadas.
- Escape vuelve al menu, avisando si hay cambios sin guardar.

Los borradores pueden estar incompletos. Para guardar una sala Activa necesita un jugador, suelo conectado y accesos despejados delante de ambas mitades de las puertas. Una sala de jefe requiere un unico B y no admite E, porque ese modo solo genera al jefe. Las salas normales no admiten B.

Las salas activas se suman a las salas originales en la seleccion aleatoria, sin reiniciar. Se guardan en `data/levels/custom/*.json`. En el ejecutable empaquetado se usa `%APPDATA%/Grimorium/rooms/`. Para retirar una sala de las partidas, abrela, cambia a Borrador y guarda.
