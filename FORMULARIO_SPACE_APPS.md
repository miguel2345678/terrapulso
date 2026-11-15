# Borradores para el formulario de Space Apps

Son borradores: ajústenlos con sus palabras y con los resultados reales que vean en la herramienta.
Los textos entre [corchetes] deben completarlos ustedes.

## Nombre del proyecto

TerraPulso  (pueden cambiarlo; también aparece en `app.py`, líneas del título)

## Resumen general (50 a 200 palabras)

TerraPulso es una herramienta web que convierte datos abiertos de la NASA en respuestas claras sobre el cambio
ambiental. El usuario elige una variable (temperatura, precipitación, humedad, viento, radiación solar, nubes o
humedad del suelo), un lugar del planeta y un período desde 1981. La herramienta muestra cómo evoluciona la
variable y responde cuatro preguntas: qué está cambiando, dónde, cuánto y si el cambio es estadísticamente
significativo. Para ello aplica métodos usados por la comunidad científica: la pendiente de Theil-Sen mide la
magnitud del cambio y la prueba de Mann-Kendall, corregida por autocorrelación, determina su significancia. Un
mapa evalúa cada celda de la región y revela cuándo una misma variable aumenta en una zona y disminuye en otra,
con control de falsos descubrimientos. Cada resultado se traduce a una frase en lenguaje sencillo, de modo que
estudiantes, agricultores y tomadores de decisiones puedan distinguir un cambio real de la variabilidad natural
sin necesidad de programar.

## Detalles del proyecto

**¿Qué hace exactamente?** Descarga series mensuales de 17 variables de NASA POWER para cualquier punto o región
(hasta 10° × 10°), calcula un valor por año o por temporada, estima la tendencia y su intervalo de confianza, y
clasifica el cambio como significativo o no al 90, 95 o 99 % de confianza.

**¿Cómo funciona?** (1) Consulta la API mensual de NASA POWER. (2) Elimina el ciclo estacional promediando los
meses elegidos. (3) Calcula la pendiente de Theil-Sen. (4) Aplica la prueba de Mann-Kendall con corrección por
autocorrelación lag-1. (5) En el mapa repite el análisis en cada celda y controla la tasa de falsos
descubrimientos (Benjamini-Hochberg). (6) Presenta gráficas interactivas, un mapa y un texto interpretativo.

**¿Qué beneficios tiene?** Reduce a segundos un análisis que normalmente exige programar; evita conclusiones
falsas al separar tendencia real de variabilidad natural; muestra contrastes regionales que un promedio oculta;
permite descargar los resultados en CSV; funciona en español.

**¿Qué esperan lograr?** [Ejemplo: que colegios, universidades y entidades del Huila puedan consultar con
evidencia cómo está cambiando su clima; ampliar la herramienta a más conjuntos de datos de la NASA.]

**Herramientas utilizadas:** Python, Streamlit (interfaz), Plotly (gráficas y mapas), NumPy, pandas, SciPy
(estadística), Requests (API). Datos de NASA POWER.

## Uso de inteligencia artificial

Sí se usó. Herramienta: Claude (Anthropic), un modelo de lenguaje (LLM).
Uso: generación del código Python, redacción de los textos de la interfaz y borradores de la documentación. El
equipo revisó, ejecutó y validó los resultados. [Agreguen aquí cualquier otra herramienta de IA que usen, por
ejemplo para imágenes o diapositivas.] El uso de IA está indicado al pie de la aplicación y en el README.
No se generaron ni modificaron logotipos, banderas ni identificadores de misiones de la NASA.

## Datos de la NASA

- NASA POWER (Prediction Of Worldwide Energy Resources), API mensual:
  https://power.larc.nasa.gov/docs/services/api/temporal/monthly/
- Portal de NASA POWER: https://power.larc.nasa.gov/
- MERRA-2, NASA Global Modeling and Assimilation Office (variables meteorológicas): https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/
- CERES (radiación y nubes, satélites Terra y Aqua): https://ceres.larc.nasa.gov/
- [Agreguen el o los recursos de la pestaña «Resources» de su desafío que hayan consultado.]

## Datos de agencias asociadas y otros recursos

- Agencias asociadas: [ninguno por ahora; es opcional]
- Streamlit: https://streamlit.io/ · Plotly: https://plotly.com/python/ · SciPy: https://scipy.org/
- Mapa base: CARTO / OpenStreetMap (© colaboradores de OpenStreetMap)
- Métodos: Mann (1945); Kendall (1975); Sen (1968); Yue y Wang (2004); Wilks (2016)
- Asistencia de IA: Claude (Anthropic)

## Guion sugerido para la demostración (7 diapositivas o video de 30 s)

1. Problema: hay muchas variables y es difícil saber cuál cambió de verdad.
2. Solución: TerraPulso en una frase + captura de pantalla.
3. ¿Cuánto?: serie de temperatura en Neiva con su tendencia y valor p.
4. ¿Qué?: gráfica de barras con todas las variables.
5. ¿Dónde?: mapa con zonas que aumentan y zonas que disminuyen.
6. Método y datos de la NASA.
7. Impacto y próximos pasos.

Recuerden: el enlace debe abrir sin contraseña; si es video, subtítulos en inglés; no incluir nombres, voces
ni imágenes de menores de 18 años.
