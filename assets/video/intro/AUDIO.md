# Audio provisional de la intro

`intro-audio.wav` acompaña el animatic de 20 segundos. Contiene un motivo
musical original de notas sintéticas tipo madera y pequeños efectos originales:
pasos, páginas, aleteos, tirón y golpe suave. La pausa tras el robo forma parte
del gag. Está pensado como una primera mezcla para probar el ritmo, no como
la banda sonora definitiva del juego.

No usa música de Kirby, grabaciones, muestras, descargas ni recursos externos.
Todo se sintetiza con `math`, `random`, `array` y `wave` de la biblioteca estándar
de Python. La semilla fija permite regenerarlo exactamente.

Formato: **20,000 segundos, estéreo, 22 050 Hz, PCM de 16 bits**. La mezcla
aplica entrada y salida suaves y deja margen bajo el nivel de saturación.

## Regeneración

Desde la raíz del proyecto:

```powershell
python tools/build_intro_audio.py
```

Si Python no está en `PATH` en este ordenador:

```powershell
& 'C:\ProgramData\anaconda3\python.exe' tools/build_intro_audio.py
```

Para guardar otra versión sin sustituir esta:

```powershell
python tools/build_intro_audio.py --out assets/video/intro/intro-audio-alternativo.wav
```

El script informa de duración, formato, pico y RMS. El volumen general se debe
ajustar en el reproductor; los efectos y la música están mezclados en este WAV.

## Sincronización

| Tiempo | Acción y audio |
| --- | --- |
| 0–4,4 s | Lectura: motivo de madera, pasos tranquilos y dos páginas. |
| 4,4–5,4 s | Sombra: aire que se acerca, la música pierde actividad. |
| 5,4–5,72 s | Robo: ráfaga rápida de derecha a izquierda y tirón. |
| 5,72–8,6 s | Reacción: pausa musical; acentos suaves a 6,2 y 7,2 s. |
| 8,6–11,6 s | Vuelo hacia la torre: cinco aleteos y notas espaciadas. |
| 11,6–17,5 s | Persecución: motivo más rápido y pasos cortos. |
| 17,5–18,8 s | Llegada: dos golpes suaves y un breve descanso. |
| 18,8–20 s | Cierre: tres notas y un acorde corto, con salida suave. |

Si cambia la duración de los planos, conviene mover los eventos del script en
lugar de acelerar todo el WAV: así se conserva el silencio del chiste.
