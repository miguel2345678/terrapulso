"""
nasa_power.py
=============
Descarga datos mensuales de NASA POWER (https://power.larc.nasa.gov/).

NASA POWER entrega, sin registro ni contraseña, variables de:
  * MERRA-2  (modelo/reanálisis de la NASA GMAO): temperatura, lluvia, humedad, viento, suelo
  * CERES SYN1deg y GEWEX SRB (misiones satelitales): radiación solar y nubes

Cada respuesta se guarda en la carpeta `datos_cache/`, así la segunda vez
la herramienta funciona al instante e incluso sin internet.

AI disclosure / Uso de IA: this code was generated with AI assistance
(Claude, by Anthropic) and was run and verified by Team UCC.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import requests

URL_BASE = "https://power.larc.nasa.gov/api/temporal/monthly"
CARPETA_CACHE = Path(__file__).parent / "datos_cache"
VALOR_FALTANTE = -900.0  # POWER usa -999 para "sin dato"
PRIMER_ANIO = 1981       # inicio de MERRA-2 en POWER (la radiación solar inicia en 1984)

# ---------------------------------------------------------------------------
# Catálogo de variables. clave = código oficial de NASA POWER.
#   escala: "calor" (rojo = aumenta) o "agua" (verde-azul = aumenta)
#   pct   : True si tiene sentido expresar el cambio en porcentaje
# ---------------------------------------------------------------------------
CATALOGO = {
    "T2M":               dict(nombre="Temperatura del aire a 2 m (media)", unidad="°C", grupo="Temperatura", fuente="MERRA-2 (modelo)", escala="calor", pct=False),
    "T2M_MAX":           dict(nombre="Temperatura máxima a 2 m", unidad="°C", grupo="Temperatura", fuente="MERRA-2 (modelo)", escala="calor", pct=False),
    "T2M_MIN":           dict(nombre="Temperatura mínima a 2 m", unidad="°C", grupo="Temperatura", fuente="MERRA-2 (modelo)", escala="calor", pct=False),
    "TS":                dict(nombre="Temperatura de la superficie terrestre", unidad="°C", grupo="Temperatura", fuente="MERRA-2 (modelo)", escala="calor", pct=False),
    "T2MDEW":            dict(nombre="Punto de rocío a 2 m", unidad="°C", grupo="Humedad", fuente="MERRA-2 (modelo)", escala="agua", pct=False),
    "PRECTOTCORR":       dict(nombre="Precipitación (corregida)", unidad="mm/día", grupo="Agua", fuente="MERRA-2 (modelo)", escala="agua", pct=True),
    "RH2M":              dict(nombre="Humedad relativa a 2 m", unidad="%", grupo="Humedad", fuente="MERRA-2 (modelo)", escala="agua", pct=False),
    "QV2M":              dict(nombre="Humedad específica a 2 m", unidad="g/kg", grupo="Humedad", fuente="MERRA-2 (modelo)", escala="agua", pct=True),
    "GWETTOP":           dict(nombre="Humedad del suelo superficial (0-1)", unidad="fracción", grupo="Agua", fuente="MERRA-2 (modelo)", escala="agua", pct=True),
    "GWETROOT":          dict(nombre="Humedad del suelo en zona de raíces (0-1)", unidad="fracción", grupo="Agua", fuente="MERRA-2 (modelo)", escala="agua", pct=True),
    "WS2M":              dict(nombre="Velocidad del viento a 2 m", unidad="m/s", grupo="Viento y presión", fuente="MERRA-2 (modelo)", escala="calor", pct=True),
    "WS10M":             dict(nombre="Velocidad del viento a 10 m", unidad="m/s", grupo="Viento y presión", fuente="MERRA-2 (modelo)", escala="calor", pct=True),
    "PS":                dict(nombre="Presión en superficie", unidad="kPa", grupo="Viento y presión", fuente="MERRA-2 (modelo)", escala="calor", pct=False),
    "ALLSKY_SFC_SW_DWN": dict(nombre="Radiación solar que llega a la superficie", unidad="MJ/m²/día", grupo="Radiación y nubes", fuente="CERES / GEWEX SRB (satélite)", escala="calor", pct=True),
    "CLRSKY_SFC_SW_DWN": dict(nombre="Radiación solar con cielo despejado", unidad="MJ/m²/día", grupo="Radiación y nubes", fuente="CERES / GEWEX SRB (satélite)", escala="calor", pct=True),
    "ALLSKY_SFC_LW_DWN": dict(nombre="Radiación infrarroja descendente", unidad="W/m²", grupo="Radiación y nubes", fuente="CERES / GEWEX SRB (satélite)", escala="calor", pct=True),
    "CLOUD_AMT":         dict(nombre="Cobertura de nubes", unidad="%", grupo="Radiación y nubes", fuente="CERES / GEWEX SRB (satélite)", escala="agua", pct=False),
}

_UNIDADES_BONITAS = {"C": "°C", "mm/day": "mm/día", "MJ/m^2/day": "MJ/m²/día",
                     "kW-hr/m^2/day": "kWh/m²/día", "W/m^2": "W/m²", "1": "fracción"}


class ErrorNASA(Exception):
    """Error legible para mostrar en pantalla."""


def _descargar_json(ruta: str, parametros: dict, intentos: int = 3) -> dict:
    """GET con caché en disco y reintentos."""
    CARPETA_CACHE.mkdir(exist_ok=True)
    firma = ruta + "?" + "&".join(f"{k}={parametros[k]}" for k in sorted(parametros))
    archivo = CARPETA_CACHE / (hashlib.sha1(firma.encode()).hexdigest()[:20] + ".json.gz")
    if archivo.exists():
        try:
            with gzip.open(archivo, "rt", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            archivo.unlink(missing_ok=True)  # caché dañada: se vuelve a descargar

    ultimo_error = "sin respuesta"
    for intento in range(intentos):
        try:
            r = requests.get(f"{URL_BASE}/{ruta}", params=parametros, timeout=180)
            if r.status_code == 200:
                datos = r.json()
                with gzip.open(archivo, "wt", encoding="utf-8") as f:
                    json.dump(datos, f)
                return datos
            ultimo_error = f"HTTP {r.status_code}: {r.text[:300]}"
            if r.status_code in (400, 404, 422):  # petición inválida: no sirve reintentar
                break
        except requests.RequestException as e:
            ultimo_error = f"problema de conexión ({type(e).__name__})"
        time.sleep(2 * (intento + 1))
    raise ErrorNASA(f"NASA POWER no respondió correctamente. Detalle: {ultimo_error}")


def _a_tabla(valores_por_fecha: dict, anios: np.ndarray) -> np.ndarray:
    """{'198101': 24.3, ..., '198113': anual} -> arreglo (n_años, 12). Ignora el mes 13."""
    tabla = np.full((len(anios), 12), np.nan)
    primero = int(anios[0])
    for clave, valor in valores_por_fecha.items():
        try:
            anio, mes = int(str(clave)[:4]), int(str(clave)[4:6])
        except ValueError:
            continue
        i = anio - primero
        if 1 <= mes <= 12 and 0 <= i < len(anios) and valor is not None and float(valor) > VALOR_FALTANTE:
            tabla[i, mes - 1] = float(valor)
    return tabla


def _unidades(datos: dict) -> dict:
    salida = {}
    for var, info in (datos.get("parameters") or {}).items():
        u = (info or {}).get("units")
        if u:
            salida[var] = _UNIDADES_BONITAS.get(u, u)
    return salida


def descargar_punto(lat: float, lon: float, variables: list[str], anio_ini: int, anio_fin: int):
    """Serie mensual de varias variables en un punto.

    Devuelve (tablas, anios, unidades, fallidas):
      tablas   : {variable: arreglo (n_años, 12)}
      fallidas : variables que la NASA no pudo entregar
    """
    anios = np.arange(anio_ini, anio_fin + 1)
    base = dict(community="AG", longitude=round(lon, 4), latitude=round(lat, 4),
                start=anio_ini, end=anio_fin, format="JSON")

    def pedir(lista):
        datos = _descargar_json("point", dict(base, parameters=",".join(lista)))
        bloque = datos.get("properties", {}).get("parameter", {})
        return {v: _a_tabla(bloque[v], anios) for v in lista if v in bloque}, _unidades(datos)

    tablas, unidades, fallidas = {}, {}, []
    try:
        tablas, unidades = pedir(variables)
    except ErrorNASA:
        if len(variables) == 1:
            raise
        for v in variables:  # si el lote falla, se pide una por una
            try:
                t, u = pedir([v])
                tablas.update(t)
                unidades.update(u)
            except ErrorNASA:
                fallidas.append(v)
        if not tablas:
            raise
    fallidas += [v for v in variables if v not in tablas and v not in fallidas]
    return tablas, anios, unidades, fallidas


def descargar_region(variable: str, lat_min: float, lat_max: float, lon_min: float,
                     lon_max: float, anio_ini: int, anio_fin: int):
    """Serie mensual de UNA variable en todas las celdas de un recuadro (máx. 10° x 10°).

    Devuelve (lats, lons, cubo, anios) con cubo de forma (n_celdas, n_años, 12).
    """
    anios = np.arange(anio_ini, anio_fin + 1)
    parametros = {"parameters": variable, "community": "AG", "format": "JSON",
                  "latitude-min": lat_min, "latitude-max": lat_max,
                  "longitude-min": lon_min, "longitude-max": lon_max,
                  "start": anio_ini, "end": anio_fin}
    datos = _descargar_json("regional", parametros)
    celdas = datos.get("features")
    if celdas is None and datos.get("type") == "Feature":
        celdas = [datos]
    lats, lons, tablas = [], [], []
    for c in celdas or []:
        try:
            coord = c["geometry"]["coordinates"]
            serie = c["properties"]["parameter"][variable]
        except (KeyError, TypeError):
            continue
        lons.append(float(coord[0]))
        lats.append(float(coord[1]))
        tablas.append(_a_tabla(serie, anios))
    if not tablas:
        raise ErrorNASA("La respuesta regional de NASA POWER llegó sin celdas de datos.")
    return np.array(lats), np.array(lons), np.stack(tablas), anios


def enlace_api_punto(lat, lon, variables, anio_ini, anio_fin) -> str:
    """Enlace reproducible (para citar en el formulario de Space Apps)."""
    return (f"{URL_BASE}/point?parameters={','.join(variables)}&community=AG"
            f"&longitude={round(lon, 4)}&latitude={round(lat, 4)}&start={anio_ini}&end={anio_fin}&format=JSON")
