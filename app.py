"""
TerraPulso - Explorador de cambios del sistema Tierra
=====================================================
NASA Space Apps Challenge 2026 (sede Neiva).

Responde cuatro preguntas con datos abiertos de la NASA (NASA POWER):
    ¿QUÉ cambia?  ¿DÓNDE cambia?  ¿CUÁNTO cambia?  ¿Es SIGNIFICATIVO?

Para ejecutarla:   streamlit run app.py

AI disclosure / Uso de IA: this code was generated with AI assistance
(Claude, by Anthropic) and was run and verified by Team UCC.
"""
from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import estadistica as est
import nasa_power as nasa
from nasa_power import CATALOGO

st.set_page_config(page_title="TerraPulso | Cambios del sistema Tierra", page_icon="🌍", layout="wide")

ANIO_MAX = date.today().year - 1  # último año completo disponible

LUGARES = {
    "Neiva, Huila (Colombia)": (2.93, -75.28),
    "Bogotá (Colombia)": (4.71, -74.07),
    "Leticia, Amazonía (Colombia)": (-4.21, -69.94),
    "Riohacha, La Guajira (Colombia)": (11.54, -72.91),
    "Niamey, Sahel (Níger)": (13.51, 2.11),
    "Utqiagvik, Ártico (Alaska)": (71.29, -156.79),
    "Mar de Aral (Asia Central)": (45.0, 60.0),
    "Otro lugar (escribir coordenadas)": None,
}

TEMPORADAS = {
    "Año completo (ene-dic)": list(range(1, 13)),
    "Dic-Ene-Feb": [12, 1, 2],
    "Mar-Abr-May": [3, 4, 5],
    "Jun-Jul-Ago": [6, 7, 8],
    "Sep-Oct-Nov": [9, 10, 11],
}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
for _i, _m in enumerate(MESES, start=1):
    TEMPORADAS[f"Solo {_m}"] = [_i]

ESCALAS = {"calor": "RdBu_r", "agua": "BrBG"}


# ------------------------------------------------------------------ utilidades
def num(x, cifras=3, signo=False):
    """Número legible con cifras significativas."""
    if x is None or not np.isfinite(x):
        return "s/d"
    texto = f"{x:+.{cifras}g}" if signo else f"{x:.{cifras}g}"
    return texto.replace("e+0", "e").replace("e-0", "e-")


def texto_p(p):
    if not np.isfinite(p):
        return "s/d"
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


@st.cache_data(show_spinner=False)
def datos_punto(lat, lon, variables, ini, fin):
    return nasa.descargar_punto(lat, lon, list(variables), ini, fin)


@st.cache_data(show_spinner=False)
def datos_region(variable, lat_min, lat_max, lon_min, lon_max, ini, fin):
    return nasa.descargar_region(variable, lat_min, lat_max, lon_min, lon_max, ini, fin)


def analizar(tabla, anios, meses, alfa, corregir):
    """Serie anual + tendencia + magnitudes del cambio para una variable."""
    serie = est.serie_estacional(tabla, meses)
    r = est.tendencia(anios, serie, alfa, corregir)
    r["serie"] = serie
    validos = np.isfinite(serie)
    if r["valido"]:
        a = anios[validos]
        r["anio_ini"], r["anio_fin"] = int(a[0]), int(a[-1])
        r["cambio_total"] = r["pendiente"] * (a[-1] - a[0])
        r["media"] = float(np.nanmean(serie))
        k = min(10, validos.sum() // 2)
        r["media_inicio"] = float(np.mean(serie[validos][:k]))
        r["media_final"] = float(np.mean(serie[validos][-k:]))
        r["k"] = int(k)
    return r


# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    st.header("1. ¿Qué variable?")
    grupos = sorted({v["grupo"] for v in CATALOGO.values()})
    grupo = st.selectbox("Tema", grupos, index=grupos.index("Temperatura"))
    opciones = [k for k, v in CATALOGO.items() if v["grupo"] == grupo]
    variable = st.selectbox("Variable", opciones, format_func=lambda k: CATALOGO[k]["nombre"])
    st.caption(f"Código NASA POWER: `{variable}` · Fuente: {CATALOGO[variable]['fuente']}")

    st.header("2. ¿Dónde?")
    lugar = st.selectbox("Lugar", list(LUGARES))
    if LUGARES[lugar] is None:
        lat = st.number_input("Latitud (−90 a 90)", -89.0, 89.0, 2.93, step=0.5, format="%.2f")
        lon = st.number_input("Longitud (−180 a 180)", -179.0, 179.0, -75.28, step=0.5, format="%.2f")
    else:
        lat, lon = LUGARES[lugar]
    medio = st.slider("Tamaño del mapa alrededor del punto (grados)", 1.0, 5.0, 3.0, 0.5,
                      help="El mapa cubre esta distancia hacia cada lado. 1° ≈ 111 km.")

    st.header("3. ¿Cuándo?")
    ini, fin = st.slider("Período de análisis", nasa.PRIMER_ANIO, ANIO_MAX, (nasa.PRIMER_ANIO, ANIO_MAX))
    temporada = st.selectbox("Época del año", list(TEMPORADAS))
    meses = TEMPORADAS[temporada]

    st.header("4. ¿Qué tan exigente?")
    confianza = st.select_slider("Nivel de confianza", [90, 95, 99], value=95, format_func=lambda c: f"{c} %")
    alfa = 1 - confianza / 100
    corregir = st.checkbox("Corregir autocorrelación", True,
                           help="Evita falsos positivos cuando cada año se parece al anterior.")
    usar_fdr = st.checkbox("Control de falsos descubrimientos en el mapa", True,
                           help="Al evaluar cientos de celdas, algunas salen 'significativas' por puro azar. "
                                "Este control (Benjamini-Hochberg) las descarta.")

if fin - ini + 1 < est.MIN_ANIOS + 1:
    st.warning(f"Elige un período de al menos {est.MIN_ANIOS + 1} años para poder evaluar tendencias.")
    st.stop()

# ------------------------------------------------------------------ encabezado
st.title("🌍 TerraPulso")
st.markdown("**Explorador de cambios del sistema Tierra** — qué cambia, dónde, cuánto y si el cambio es "
            "estadísticamente significativo, con datos abiertos de la NASA.")

# ------------------------------------------------------------------ datos del punto
todas = tuple(CATALOGO)
try:
    with st.spinner("Descargando datos de NASA POWER (la primera vez tarda unos segundos)…"):
        tablas, anios, unidades_api, fallidas = datos_punto(lat, lon, todas, ini, fin)
except nasa.ErrorNASA as e:
    st.error(f"No se pudieron obtener los datos. {e}")
    st.info("Revisa la conexión a internet y vuelve a intentar. Si el error menciona el año final, "
            "reduce el período en la barra lateral.")
    st.stop()


def unidad(v):
    return unidades_api.get(v, CATALOGO[v]["unidad"])


if variable not in tablas:
    st.error(f"NASA POWER no entregó la variable {variable} para este lugar. Elige otra variable.")
    st.stop()

info = CATALOGO[variable]
u = unidad(variable)
r = analizar(tablas[variable], anios, meses, alfa, corregir)

def mostrar_mapa(clave, lat_min, lat_max, lon_min, lon_max):
    try:
        with st.spinner("Descargando la región desde NASA POWER…"):
            lats, lons, cubo, anios_r = datos_region(*clave)
    except nasa.ErrorNASA as e:
        st.error(f"No se pudo descargar la región. {e}")
        return
    cubo_anual = est.serie_estacional(cubo, meses)
    t = est.tendencia_por_celda(anios_r, cubo_anual, alfa, corregir)
    con_dato = np.isfinite(t["p"])
    if not con_dato.any():
        st.warning("Ninguna celda tiene años suficientes con datos en este período.")
        return
    sig = est.fdr_benjamini_hochberg(t["p"], alfa) if usar_fdr else (t["p"] < alfa)
    sig = sig & con_dato
    dec = t["pendiente"] * 10
    n = int(con_dato.sum())
    n_sube, n_baja = int((sig & (dec > 0)).sum()), int((sig & (dec < 0)).sum())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Celdas analizadas", n)
    m2.metric("Aumento significativo", f"{100 * n_sube / n:.0f} %")
    m3.metric("Disminución significativa", f"{100 * n_baja / n:.0f} %")
    m4.metric("Sin cambio significativo", f"{100 * (n - n_sube - n_baja) / n:.0f} %")
    if n_sube and n_baja:
        st.warning("En esta región la misma variable **aumenta en unas zonas y disminuye en otras**. "
                   "Un único promedio regional ocultaría este contraste.")

    tope = float(np.nanpercentile(np.abs(dec[con_dato]), 98)) or 1.0
    figm = go.Figure()
    for mascara, tam, opac, nombre in ((con_dato & ~sig, 8, 0.5, "No significativo (punto pequeño)"),
                                       (sig, 17, 0.95, "Significativo (punto grande)")):
        if mascara.any():
            figm.add_trace(go.Scattermap(
                lat=lats[mascara], lon=lons[mascara], mode="markers", name=nombre,
                marker=dict(size=tam, opacity=opac, color=dec[mascara], coloraxis="coloraxis"),
                customdata=np.stack([dec[mascara], t["p"][mascara]], axis=1),
                text=[texto_p(v) for v in t["p"][mascara]],
                hovertemplate="Lat %{lat:.2f}, Lon %{lon:.2f}<br>%{customdata[0]:+.3g} " + u +
                              "/década<br>p = %{text}<extra>" + nombre.split(" (")[0] + "</extra>"))
    figm.add_trace(go.Scattermap(lat=[lat], lon=[lon], mode="markers", name="Punto analizado",
                                 marker=dict(size=11, color="black"), hoverinfo="name"))
    figm.update_layout(
        height=600, margin=dict(l=0, r=0, t=0, b=0),
        map=dict(style="carto-positron", center=dict(lat=(lat_min + lat_max) / 2, lon=(lon_min + lon_max) / 2),
                 zoom=float(np.clip(8.3 - np.log2(max(lat_max - lat_min, lon_max - lon_min)), 1, 9))),
        coloraxis=dict(colorscale=ESCALAS[info["escala"]], cmin=-tope, cmax=tope,
                       colorbar=dict(title=f"{u}/década")),
        legend=dict(orientation="h", y=1.02, bgcolor="rgba(255,255,255,0.7)"))
    st.plotly_chart(figm, width="stretch")
    st.caption("Color: dirección y magnitud de la tendencia por década. Tamaño: significancia estadística"
               + (" (con control de falsos descubrimientos)." if usar_fdr else "."))

    # Promedio regional ponderado por área (coseno de la latitud)
    pesos = np.cos(np.deg2rad(lats))[:, None] * np.isfinite(cubo_anual)
    with np.errstate(invalid="ignore", divide="ignore"):
        prom = np.nansum(cubo_anual * pesos, axis=0) / pesos.sum(axis=0)
    rr = est.tendencia(anios_r, prom, alfa, corregir)
    if rr["valido"]:
        st.markdown(f"**Promedio de toda la región:** {num(rr['pendiente'] * 10, signo=True)} {u}/década, "
                    f"p = {texto_p(rr['p'])} → {'significativo' if rr['significativo'] else 'no significativo'} "
                    f"al {confianza} %.")
    celdas = pd.DataFrame({"lat": lats, "lon": lons, f"tendencia ({u}/decada)": dec,
                           "valor_p": t["p"], "significativo": sig})
    st.download_button("Descargar resultados del mapa (CSV)", celdas.to_csv(index=False).encode("utf-8"),
                       f"mapa_{variable}.csv", "text/csv")


pestana_cuanto, pestana_que, pestana_donde, pestana_metodo = st.tabs(
    ["📈 ¿Cuánto cambia?", "🧭 ¿Qué está cambiando?", "🗺️ ¿Dónde cambia?", "📚 Método y fuentes"])

# ================================================================== ¿CUÁNTO?
with pestana_cuanto:
    st.subheader(f"{info['nombre']} · {lugar.split(' (')[0] if LUGARES[lugar] else f'{lat:.2f}°, {lon:.2f}°'}")
    if not r["valido"]:
        st.warning(f"No hay suficientes años con datos completos (se necesitan {est.MIN_ANIOS}; hay {r['n']}). "
                   "Las variables de radiación y nubes empiezan en 1984. Amplía el período o cambia la variable.")
    else:
        por_decada = r["pendiente"] * 10
        sube = r["pendiente"] > 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"Tendencia por década ({u})", num(por_decada, signo=True))
        c2.metric(f"Cambio {r['anio_ini']}–{r['anio_fin']} ({u})", num(r['cambio_total'], signo=True))
        c3.metric("Valor p (Mann-Kendall)", texto_p(r["p"]))
        c4.metric("¿Significativo?", ("Sí" if r["significativo"] else "No") + f" (al {confianza} %)")

        verbo = "aumentó" if sube else "disminuyó"
        pct = ""
        if info["pct"] and r["media"] != 0:
            pct = f", es decir {num(100 * r['cambio_total'] / abs(r['media']), 2, True)} % respecto al promedio del período"
        if r["significativo"]:
            st.success(
                f"**Cambio significativo.** {info['nombre']} {verbo} a un ritmo de "
                f"**{num(abs(por_decada))} {u} por década** (intervalo al {confianza} %: "
                f"{num(r['pend_inf'] * 10, signo=True)} a {num(r['pend_sup'] * 10, signo=True)}). "
                f"En total: {num(r['cambio_total'], signo=True)} {u} entre {r['anio_ini']} y {r['anio_fin']}{pct}. "
                f"La probabilidad de observar una tendencia así por puro azar es p = {texto_p(r['p'])}.")
        else:
            st.info(
                f"**Sin cambio significativo.** La tendencia estimada es {num(por_decada, signo=True)} {u} por década, "
                f"pero con p = {texto_p(r['p'])} no se puede distinguir de la variabilidad natural al {confianza} % "
                f"de confianza. Esto no prueba que no haya cambio: solo que estos datos no alcanzan para afirmarlo.")
        st.caption(
            f"Promedio de los primeros {r['k']} años: {num(r['media_inicio'], 4)} {u} · "
            f"promedio de los últimos {r['k']} años: {num(r['media_final'], 4)} {u} · "
            f"diferencia: {num(r['media_final'] - r['media_inicio'], signo=True)} {u} · "
            f"años usados: {r['n']} · autocorrelación lag-1: {num(r['r1'], 2)}"
            + (f" (varianza corregida ×{num(r['factor'], 3)})" if r["factor"] > 1 else ""))

        # --- Gráfica de la serie anual con la recta de Theil-Sen
        serie = r["serie"]
        ok = np.isfinite(serie)
        x = anios[ok].astype(float)
        recta = r["intercepto"] + r["pendiente"] * x
        xm, ym = np.median(x), np.median(serie[ok])
        banda_a = ym + r["pend_inf"] * (x - xm)
        banda_b = ym + r["pend_sup"] * (x - xm)
        color = "#c0392b" if (sube == (info["escala"] == "calor")) else "#1f6fb2"
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=np.r_[x, x[::-1]], y=np.r_[np.maximum(banda_a, banda_b), np.minimum(banda_a, banda_b)[::-1]],
                                 fill="toself", fillcolor="rgba(120,120,120,0.18)", line=dict(width=0),
                                 name=f"Incertidumbre de la tendencia ({confianza} %)", hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=x, y=serie[ok], mode="lines+markers", name="Valor de cada año",
                                 line=dict(color="#555", width=1.5), marker=dict(size=6),
                                 hovertemplate="%{x:.0f}: %{y:.3f} " + u + "<extra></extra>"))
        fig.add_trace(go.Scatter(x=x, y=recta, mode="lines", name="Tendencia (Theil-Sen)",
                                 line=dict(color=color, width=3, dash=None if r["significativo"] else "dash"),
                                 hoverinfo="skip"))
        fig.update_layout(height=430, margin=dict(l=10, r=10, t=40, b=10), hovermode="x unified",
                          title=f"{temporada}: un valor por año", yaxis_title=f"{info['nombre']} ({u})",
                          xaxis_title="Año", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, width="stretch")

        # --- Mapa de calor mes x año de anomalías
        con_datos = np.isfinite(tablas[variable]).any(axis=1)
        tabla = tablas[variable][con_datos]
        anomalia = tabla - np.nanmean(tabla, axis=0, keepdims=True)
        tope = float(np.nanpercentile(np.abs(anomalia), 98)) if np.isfinite(anomalia).any() else 1.0
        fig2 = go.Figure(go.Heatmap(z=anomalia.T, x=anios[con_datos], y=MESES, colorscale=ESCALAS[info["escala"]],
                                    zmin=-tope, zmax=tope, colorbar=dict(title=u),
                                    hovertemplate="%{y} %{x}: %{z:+.3f} " + u + "<extra></extra>"))
        fig2.update_layout(height=360, margin=dict(l=10, r=10, t=40, b=10), yaxis=dict(autorange="reversed"),
                           title="¿En qué meses y años se nota el cambio? (diferencia frente al promedio de cada mes)")
        st.plotly_chart(fig2, width="stretch")

        descarga = pd.DataFrame({"anio": anios, f"{variable} ({u})": serie})
        st.download_button("Descargar esta serie (CSV)", descarga.to_csv(index=False).encode("utf-8"),
                           f"serie_{variable}_{lat:.2f}_{lon:.2f}.csv", "text/csv")

# ================================================================== ¿QUÉ?
with pestana_que:
    st.subheader("Todas las variables en este lugar, ordenadas por la fuerza de la señal")
    st.markdown("Cada barra es el estadístico **Z de Mann-Kendall**: mientras más lejos de cero, más clara es la "
                "tendencia. Fuera de las líneas punteadas, el cambio es significativo.")
    filas = []
    for v, tabla_v in tablas.items():
        rv = analizar(tabla_v, anios, meses, alfa, corregir)
        if not rv["valido"]:
            continue
        filas.append({
            "Variable": CATALOGO[v]["nombre"], "Código": v, "Unidad": unidad(v),
            "Tendencia por década": rv["pendiente"] * 10, "Cambio total": rv["cambio_total"],
            "Z": rv["z"], "Valor p": rv["p"],
            "Dirección": "Aumenta" if rv["pendiente"] > 0 else ("Disminuye" if rv["pendiente"] < 0 else "Estable"),
            "Significativo": "Sí" if rv["significativo"] else "No",
            "Período": f"{rv['anio_ini']}–{rv['anio_fin']}", "Fuente": CATALOGO[v]["fuente"],
        })
    if not filas:
        st.warning("No hay variables con datos suficientes en este período.")
    else:
        df = pd.DataFrame(filas).sort_values("Z", key=np.abs, ascending=False).reset_index(drop=True)
        n_sig = int((df["Significativo"] == "Sí").sum())
        st.markdown(f"**{n_sig} de {len(df)} variables** muestran un cambio significativo al {confianza} % "
                    f"({temporada.lower()}, {ini}–{fin}).")
        z_crit = float(est.stats.norm.ppf(1 - alfa / 2))
        d = df.iloc[::-1]
        colores = np.where(d["Significativo"] == "Sí", np.where(d["Z"] > 0, "#c0392b", "#1f6fb2"), "#b8b8b8")
        figz = go.Figure(go.Bar(x=d["Z"], y=d["Variable"], orientation="h", marker_color=colores,
                                customdata=np.stack([d["Tendencia por década"].map(lambda v: num(v, signo=True)),
                                                     d["Unidad"], d["Valor p"].map(texto_p)], axis=1),
                                hovertemplate="%{y}<br>Z = %{x:.2f}<br>%{customdata[0]} %{customdata[1]}/década"
                                              "<br>p = %{customdata[2]}<extra></extra>"))
        for zc in (-z_crit, z_crit):
            figz.add_vline(x=zc, line_dash="dot", line_color="#444")
        figz.update_layout(height=40 + 30 * len(d), margin=dict(l=10, r=10, t=30, b=10),
                           xaxis_title="← disminuye      Z de Mann-Kendall      aumenta →")
        st.plotly_chart(figz, width="stretch")
        st.caption("Rojo: aumento significativo · Azul: disminución significativa · Gris: no significativo.")
        st.dataframe(df.assign(**{"Valor p": df["Valor p"].map(texto_p)}), width="stretch", hide_index=True,
                     column_config={"Tendencia por década": st.column_config.NumberColumn(format="%.3g"),
                                    "Cambio total": st.column_config.NumberColumn(format="%.3g"),
                                    "Z": st.column_config.NumberColumn(format="%.2f")})
        st.download_button("Descargar tabla (CSV)", df.to_csv(index=False).encode("utf-8"),
                           f"variables_{lat:.2f}_{lon:.2f}.csv", "text/csv")
    if fallidas:
        st.caption("Variables no entregadas por NASA POWER en esta consulta: " + ", ".join(fallidas))

# ================================================================== ¿DÓNDE?
with pestana_donde:
    lat_min, lat_max = max(-90.0, round((lat - medio) * 2) / 2), min(90.0, round((lat + medio) * 2) / 2)
    lon_min, lon_max = max(-180.0, round((lon - medio) * 2) / 2), min(180.0, round((lon + medio) * 2) / 2)
    st.subheader(f"Mapa de tendencias: {info['nombre']}")
    st.markdown(f"Recuadro: latitud {lat_min}° a {lat_max}°, longitud {lon_min}° a {lon_max}°. "
                "La misma variable puede subir en una zona y bajar en otra: el mapa lo muestra celda por celda.")
    clave = (variable, lat_min, lat_max, lon_min, lon_max, ini, fin)
    if st.button("Calcular mapa", type="primary"):
        st.session_state["mapa"] = clave
    if st.session_state.get("mapa") != clave:
        st.info("Pulsa **Calcular mapa**. La primera descarga de una región puede tardar hasta un minuto; "
                "después queda guardada.")
    else:
        mostrar_mapa(clave, lat_min, lat_max, lon_min, lon_max)

# ================================================================== MÉTODO
with pestana_metodo:
    st.subheader("¿Cómo decide la herramienta si un cambio es «significativo»?")
    st.markdown(f"""
1. **Un valor por año.** Se promedian los meses elegidos ({temporada.lower()}). Un año solo cuenta si tiene todos
   sus meses; así se elimina el ciclo estacional.
2. **¿Cuánto cambia? — Pendiente de Theil-Sen.** Es la mediana de las pendientes entre todos los pares de años.
   A diferencia de una recta de mínimos cuadrados, un año extremo (por ejemplo, un Niño fuerte) no la distorsiona.
3. **¿Es significativo? — Prueba de Mann-Kendall.** Cuenta cuántos pares de años suben y cuántos bajan. El
   **valor p** es la probabilidad de ver una tendencia así de clara si en realidad no hubiera ninguna. Si
   p < {alfa:.2f}, el cambio se declara significativo al {confianza} %.
4. **Autocorrelación.** Si cada año se parece al anterior, la prueba se vuelve demasiado optimista. Se corrige
   inflando la varianza según la autocorrelación lag-1 de los residuos (Yue y Wang, 2004).
5. **Muchas pruebas a la vez.** En el mapa se evalúan cientos de celdas; con 95 % de confianza, ~5 % saldrían
   significativas por azar. El control de la tasa de falsos descubrimientos (Benjamini-Hochberg; Wilks, 2016) lo evita.

**Limitaciones.** «Significativo» quiere decir *distinguible del azar*, no necesariamente *importante*, y la prueba
no explica la causa del cambio. Las variables de MERRA-2 provienen de un modelo que asimila observaciones
(reanálisis), con celdas de ~50 km: no reemplazan una estación meteorológica local. La prueba detecta tendencias
monótonas (siempre hacia el mismo lado), no ciclos.
""")
    st.subheader("Datos de la NASA utilizados")
    st.markdown(f"""
- **NASA POWER** (Prediction Of Worldwide Energy Resources), NASA Langley Research Center — API mensual:
  https://power.larc.nasa.gov/
- **MERRA-2** (NASA GMAO): temperatura, precipitación, humedad, viento, presión y humedad del suelo, desde 1981.
- **CERES SYN1deg** (instrumentos CERES en los satélites Terra y Aqua) y **GEWEX SRB**: radiación y nubes, desde 1984.
- Consulta reproducible de esta pantalla:
  [{variable} en {lat:.2f}°, {lon:.2f}°]({nasa.enlace_api_punto(lat, lon, [variable], ini, fin)})
""")
    st.subheader("Referencias")
    st.markdown("""
- Mann (1945), *Econometrica* 13; Kendall (1975), *Rank Correlation Methods*.
- Sen (1968), *J. Am. Stat. Assoc.* 63 — pendiente e intervalo de confianza.
- Yue y Wang (2004), *Water Resources Management* 18 — corrección por autocorrelación.
- Wilks (2016), *Bull. Amer. Meteor. Soc.* 97 — falsos descubrimientos en mapas.
""")

st.divider()
st.caption("Datos: NASA POWER (NASA Langley Research Center). Proyecto del NASA Space Apps Challenge 2026; "
           "no está afiliado a la NASA ni cuenta con su respaldo. Código y textos desarrollados con asistencia "
           "de inteligencia artificial (Claude, de Anthropic).")
