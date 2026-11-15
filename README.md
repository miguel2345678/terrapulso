# TerraPulso — Earth System Change Explorer

**Team UCC · NASA Space Apps Challenge 2026 (Neiva, Colombia) · Challenge: Be An Earth System Trend Detective!**

## English summary

TerraPulso is a web tool (Python + Streamlit) that lets anyone select Earth science variables from NASA POWER
(MERRA-2 model and CERES satellite data, 1981 to present), visualize how they change over time, and determine
**what** is changing, **where**, **how much**, and whether the change is statistically **significant**
(Theil-Sen slope, Mann-Kendall test with lag-1 autocorrelation correction, and Benjamini-Hochberg false
discovery rate control on the map). The interface is in Spanish.

Run it: `pip install -r requirements.txt` then `streamlit run app.py`.

**AI disclosure:** the code, interface texts and documentation were generated with AI assistance (Claude, by
Anthropic). Team UCC ran the tool with real NASA data and verified the results. This project is not affiliated
with or endorsed by NASA and uses no NASA logos.

---

## Documentación en español

Proyecto para el NASA Space Apps Challenge 2026 (sede Neiva).

Herramienta que permite elegir una variable de ciencias de la Tierra, ver cómo cambia en el tiempo y responder:

| Pregunta del desafío | Dónde se responde en la herramienta |
|---|---|
| ¿Qué está cambiando? | Pestaña **¿Qué está cambiando?**: compara 17 variables en el mismo lugar |
| ¿Dónde está cambiando? | Pestaña **¿Dónde cambia?**: mapa de tendencias celda por celda |
| ¿Cuánto está cambiando? | Pestaña **¿Cuánto cambia?**: tendencia por década y cambio total |
| ¿Es significativo? | Prueba de Mann-Kendall en todas las pestañas |

Datos: **NASA POWER** (MERRA-2, CERES, GEWEX SRB), de 1981 al último año completo. No requiere registro.

## Archivos

```
proyecto_nasa_la_tierra/
├── app.py                 Interfaz (lo que se ve en pantalla)
├── nasa_power.py          Descarga los datos de la NASA y los guarda en caché
├── estadistica.py         Mann-Kendall, Theil-Sen, autocorrelación, falsos descubrimientos
├── requirements.txt       Librerías necesarias
├── iniciar.bat            Doble clic en Windows: instala y abre la herramienta
├── .streamlit/config.toml Configuración visual
├── pruebas/verificar.py   Comprueba cálculos y conexión con la NASA
└── datos_cache/           Se crea sola; guarda lo ya descargado
```

## Instalación paso a paso (Windows)

1. Instala **Python 3.10 o superior** desde https://www.python.org/downloads/. En la primera pantalla del
   instalador marca **"Add python.exe to PATH"**.
2. Descomprime el zip de modo que la carpeta `proyecto_nasa_la_tierra` contenga directamente `app.py`.
3. Haz **doble clic en `iniciar.bat`**. La primera vez instala las librerías (2 a 5 minutos, con internet).
4. Se abre el navegador en `http://localhost:8501`. Para cerrar: cierra la ventana negra.

### Instalación manual (Windows, Mac o Linux)

Abre una terminal dentro de la carpeta del proyecto y ejecuta:

```
python -m venv .venv
.venv\Scripts\activate            (en Mac/Linux:  source .venv/bin/activate)
pip install -r requirements.txt
python pruebas/verificar.py
streamlit run app.py
```

`verificar.py` debe terminar con "Todo listo". Si falla en el paso 2, es un problema de internet o de la API.

## Cómo usarla

1. Barra lateral: elige **variable**, **lugar**, **período** y **época del año**.
2. **¿Cuánto cambia?** muestra la tendencia, el valor p y una frase lista para leer.
3. **¿Qué está cambiando?** ordena todas las variables por la fuerza de su señal.
4. **¿Dónde cambia?** → botón **Calcular mapa** (la primera vez puede tardar hasta un minuto).
5. Cada pestaña tiene un botón para descargar los resultados en CSV.

**Antes de presentar:** abre con internet cada lugar y cada mapa que vayan a mostrar. Quedan guardados en
`datos_cache/` y después cargan al instante, aunque falle el wifi (el fondo del mapa sí necesita internet).

## Publicarla con un enlace público (opcional, gratis)

1. Suban la carpeta a un repositorio **público** de GitHub.
2. En https://share.streamlit.io inicien sesión con GitHub → **Create app** → elijan el repositorio y `app.py`.
3. Obtendrán un enlace `https://....streamlit.app` que abre sin contraseña.

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| "No se encontró Python" | Reinstalar Python marcando "Add python.exe to PATH" |
| "No se pudieron obtener los datos" | Revisar internet; reintentar en un minuto; reducir el año final |
| Una variable dice que no hay años suficientes | Radiación y nubes empiezan en 1984; ampliar el período |
| El mapa tarda mucho | Reducir el tamaño del mapa a 2° o el período |
| Quiero forzar una descarga nueva | Borrar la carpeta `datos_cache/` |

## Créditos y avisos

- Datos: NASA POWER, NASA Langley Research Center — https://power.larc.nasa.gov/
- Este proyecto no está afiliado a la NASA ni cuenta con su respaldo, y no usa logotipos de la NASA.
- Código y textos desarrollados con asistencia de inteligencia artificial (Claude, de Anthropic).
