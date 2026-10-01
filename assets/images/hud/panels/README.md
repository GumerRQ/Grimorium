# Paneles editables del HUD

Estos PNG son recortes exactos de combat_hud.png, conservando sus pixeles y transparencia:

- stats_panel.png: bloque izquierdo, con tiempo, monedas, estadisticas e iconos (73 x 167).
- tower_panel.png: marco de la torre (63 x 275).

El juego utiliza ahora estos archivos independientes. El combat_hud.png original se conserva como referencia; editarlo ya no cambia el HUD.

En una sala, pulsa F8:

- G alterna Todo / Graficos / Contenido. En Graficos, arrastra un panel completo con sus numeros.
- En Contenido puedes recolocar cada numero sin mover el dibujo.
- Anadir PNG (Ctrl+O) permite incorporar mas marcos o paneles, por ejemplo vida u objetos. Los PNG externos se copian a esta carpeta sin sobrescribir otros archivos.
- Para asociar numeros a un nuevo panel, usa Todo, selecciona el panel y los elementos con Shift+clic y pulsa Vincular (Ctrl+G). La vinculacion sustituye la lista de contenido del panel seleccionado. Seleccionar solo el panel y vincular lo deja sin contenido asociado.
- R recarga los PNG tras editarlos en Aseprite, conservando sus posiciones y tamanos en pantalla.
- Ver / ocultar (Supr) oculta solo el dibujo seleccionado, no sus numeros.
- Ctrl+S guarda; F8 guarda y sale; Escape descarta los cambios no guardados. Las posiciones y asociaciones se guardan en data/hud_layout.json.

Los paneles nuevos son graficos decorativos: anadir un PNG no crea nuevas estadisticas ni logica de objetos. Los PNG importados permanecen en esta carpeta aunque canceles su colocacion.
