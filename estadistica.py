"""
estadistica.py
==============
Pruebas estadísticas para decidir si un cambio es "significativo".

Métodos (estándar en ciencias de la Tierra):
  * Prueba de Mann-Kendall  -> ¿existe una tendencia monótona? (valor p)
  * Pendiente de Theil-Sen  -> ¿cuánto cambia por año? (robusta a valores atípicos)
  * Corrección por autocorrelación lag-1 (aproximación AR(1), enfoque de
    Yue & Wang 2004): evita "falsos positivos" cuando un año se parece al anterior.
  * Control de la Tasa de Falsos Descubrimientos (Benjamini-Hochberg, ver
    Wilks 2016) para mapas con muchas celdas evaluadas a la vez.

AI disclosure / Uso de IA: this code was generated with AI assistance
(Claude, by Anthropic) and was run and verified by Team UCC.
"""
from __future__ import annotations

import numpy as np
from scipy import stats

MIN_ANIOS = 10  # mínimo de años válidos para calcular una tendencia


def serie_estacional(tabla: np.ndarray, meses: list[int]) -> np.ndarray:
    """Convierte datos mensuales en un valor por año.

    tabla : arreglo (..., n_años, 12) con los 12 meses de cada año.
    meses : meses a promediar, p. ej. [1..12] (anual) o [12, 1, 2] (dic-ene-feb).
            Si la lista "cruza" el año (12, 1, 2), diciembre se toma del año anterior.
    Un año solo es válido si tiene TODOS los meses pedidos (si no, queda NaN).
    """
    tabla = np.asarray(tabla, dtype=float)
    ultimo = meses[-1]
    partes = []
    for m in meses:
        col = tabla[..., m - 1]
        if m > ultimo:  # mes que pertenece al año anterior (p. ej. diciembre en DEF)
            relleno = np.full(col[..., :1].shape, np.nan)
            col = np.concatenate([relleno, col[..., :-1]], axis=-1)
        partes.append(col)
    return np.mean(np.stack(partes, axis=0), axis=0)


def tendencia(anios, valores, alfa: float = 0.05, corregir_autocorr: bool = True) -> dict:
    """Mann-Kendall + Theil-Sen para una serie anual.

    Devuelve un diccionario con:
      valido      : True si hubo datos suficientes
      n           : número de años usados
      pendiente   : cambio por año (Theil-Sen)
      pend_inf/sup: intervalo de confianza de la pendiente (nivel 1-alfa)
      intercepto  : para dibujar la recta  y = intercepto + pendiente * año
      z, p        : estadístico y valor p de Mann-Kendall (dos colas)
      significativo: p < alfa
      r1          : autocorrelación lag-1 de los residuos
      factor      : factor de inflación de varianza aplicado (1 = sin corrección)
    """
    x = np.asarray(anios, dtype=float)
    y = np.asarray(valores, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    n = len(y)
    res = dict(valido=False, n=n, pendiente=np.nan, pend_inf=np.nan, pend_sup=np.nan,
               intercepto=np.nan, z=np.nan, p=np.nan, significativo=False,
               r1=np.nan, factor=1.0, s=np.nan)
    if n < MIN_ANIOS:
        return res

    iu = np.triu_indices(n, k=1)
    dy = (y[None, :] - y[:, None])[iu]
    dx = (x[None, :] - x[:, None])[iu]

    # --- Estadístico S de Mann-Kendall y su varianza (con corrección por empates)
    s = float(np.sign(dy).sum())
    _, cuentas = np.unique(y, return_counts=True)
    var_s = (n * (n - 1) * (2 * n + 5) - np.sum(cuentas * (cuentas - 1) * (2 * cuentas + 5))) / 18.0

    # --- Pendiente de Theil-Sen (mediana de todas las pendientes entre pares)
    pendientes = np.sort(dy / dx)
    pendiente = float(np.median(pendientes))
    intercepto = float(np.median(y) - pendiente * np.median(x))

    # --- Autocorrelación lag-1 de los residuos (serie sin tendencia)
    resid = y - (intercepto + pendiente * x)
    resid = resid - resid.mean()
    den = float(np.sum(resid ** 2))
    r1 = float(np.sum(resid[:-1] * resid[1:]) / den) if den > 0 else 0.0
    factor = 1.0
    if corregir_autocorr:
        umbral = (-1 + 1.645 * np.sqrt(n - 2)) / (n - 1)  # r1 positivo y significativo
        if r1 > umbral:
            r = min(r1, 0.9)
            factor = (1 + r) / (1 - r)
    var_corr = var_s * factor

    # --- Z y valor p (dos colas, con corrección de continuidad)
    if var_corr <= 0:
        z, p = 0.0, 1.0
    else:
        z = (s - np.sign(s)) / np.sqrt(var_corr)
        p = float(2 * stats.norm.sf(abs(z)))

    # --- Intervalo de confianza de la pendiente (método de Sen, 1968)
    N = len(pendientes)
    c = stats.norm.ppf(1 - alfa / 2) * np.sqrt(max(var_corr, 0.0))
    i_inf = int(np.clip(round((N - c) / 2) - 1, 0, N - 1))
    i_sup = int(np.clip(round((N + c) / 2), 0, N - 1))

    res.update(valido=True, pendiente=pendiente, pend_inf=float(pendientes[i_inf]),
               pend_sup=float(pendientes[i_sup]), intercepto=intercepto, z=float(z), p=p,
               significativo=bool(p < alfa), r1=r1, factor=factor, s=s)
    return res


def fdr_benjamini_hochberg(valores_p, alfa: float = 0.05) -> np.ndarray:
    """Devuelve una máscara booleana: True donde el resultado sigue siendo
    significativo después de controlar la tasa de falsos descubrimientos."""
    p = np.asarray(valores_p, dtype=float)
    mascara = np.zeros(p.shape, dtype=bool)
    validos = np.flatnonzero(np.isfinite(p))
    m = len(validos)
    if m == 0:
        return mascara
    orden = validos[np.argsort(p[validos])]
    umbrales = alfa * np.arange(1, m + 1) / m
    cumple = p[orden] <= umbrales
    if cumple.any():
        k = np.max(np.flatnonzero(cumple))
        mascara[orden[: k + 1]] = True
    return mascara


def tendencia_por_celda(anios, cubo_anual: np.ndarray, alfa: float = 0.05,
                        corregir_autocorr: bool = True) -> dict:
    """Aplica `tendencia` a cada celda de un mapa. cubo_anual: (n_celdas, n_años)."""
    n = cubo_anual.shape[0]
    pend = np.full(n, np.nan)
    p = np.full(n, np.nan)
    z = np.full(n, np.nan)
    for i in range(n):
        r = tendencia(anios, cubo_anual[i], alfa, corregir_autocorr)
        if r["valido"]:
            pend[i], p[i], z[i] = r["pendiente"], r["p"], r["z"]
    return dict(pendiente=pend, p=p, z=z)
