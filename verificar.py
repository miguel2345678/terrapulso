"""
verificar.py - Comprueba que todo está listo antes de la presentación.

Ejecutar desde la carpeta del proyecto:
    python pruebas/verificar.py

1) Valida los cálculos estadísticos contra SciPy.
2) Hace una consulta real a NASA POWER (necesita internet).

AI disclosure / Uso de IA: this code was generated with AI assistance
(Claude, by Anthropic) and was run and verified by Team UCC.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from scipy import stats

import estadistica as est
import nasa_power as nasa


def probar_estadistica():
    rng = np.random.default_rng(42)
    anios = np.arange(1981, 2026)

    # a) Serie con tendencia real: debe detectarse y la pendiente debe coincidir con SciPy
    y = 0.03 * (anios - 1981) + rng.normal(0, 0.25, anios.size)
    r = est.tendencia(anios, y, corregir_autocorr=False)
    pendiente_scipy = stats.theilslopes(y, anios)[0]
    tau, p_scipy = stats.kendalltau(anios, y)
    assert abs(r["pendiente"] - pendiente_scipy) < 1e-12, "Theil-Sen no coincide con SciPy"
    assert r["significativo"] and p_scipy < 0.05, "No detectó una tendencia evidente"
    assert abs(np.log10(r["p"]) - np.log10(p_scipy)) < 0.5, "Valor p lejos del de SciPy"
    assert r["pend_inf"] < 0.03 < r["pend_sup"], "El intervalo no contiene la pendiente real"

    # b) Ruido puro: ~5 % de falsos positivos al 95 %
    falsos = np.mean([est.tendencia(anios, rng.normal(size=anios.size), corregir_autocorr=False)["significativo"]
                      for _ in range(2000)])
    assert 0.03 < falsos < 0.07, f"Tasa de falsos positivos fuera de rango: {falsos:.3f}"

    # c) Ruido autocorrelacionado: la corrección debe reducir los falsos positivos
    def ar1():
        e = rng.normal(size=anios.size)
        for i in range(1, e.size):
            e[i] += 0.6 * e[i - 1]
        return e
    series = [ar1() for _ in range(1000)]
    sin = np.mean([est.tendencia(anios, s, corregir_autocorr=False)["significativo"] for s in series])
    con = np.mean([est.tendencia(anios, s, corregir_autocorr=True)["significativo"] for s in series])
    assert con < sin and con < 0.12, f"La corrección de autocorrelación no funciona ({sin:.2f} -> {con:.2f})"

    # d) Falsos descubrimientos: con 500 celdas de ruido, casi ninguna debe quedar
    p = rng.uniform(size=500)
    assert est.fdr_benjamini_hochberg(p).sum() <= 2
    assert est.fdr_benjamini_hochberg(np.r_[np.full(50, 1e-6), p]).sum() >= 50

    # e) Temporada que cruza el año (dic-ene-feb) y años incompletos
    tabla = np.arange(36, dtype=float).reshape(3, 12)
    def_ = est.serie_estacional(tabla, [12, 1, 2])
    assert np.isnan(def_[0]) and def_[1] == np.mean([11, 12, 13])
    tabla[2, 5] = np.nan
    assert np.isnan(est.serie_estacional(tabla, list(range(1, 13)))[2])
    print(f"  Estadística correcta  (falsos positivos: {falsos:.1%}; con autocorrelación {sin:.0%} -> {con:.0%})")


def probar_nasa():
    tablas, anios, unidades, fallidas = nasa.descargar_punto(2.93, -75.28, ["T2M", "PRECTOTCORR"], 2015, 2020)
    t = tablas["T2M"]
    assert t.shape == (6, 12) and np.isfinite(t).all(), "Datos incompletos de T2M"
    assert 10 < t.mean() < 35, f"Temperatura de Neiva fuera de lo esperado: {t.mean():.1f}"
    print(f"  Conexión con NASA POWER correcta  (T2M media en Neiva 2015-2020: {t.mean():.1f} {unidades.get('T2M', '')})")
    lats, lons, cubo, _ = nasa.descargar_region("T2M", 2.0, 4.0, -76.0, -74.0, 2019, 2020)
    assert cubo.shape[0] == lats.size > 1 and np.isfinite(cubo).any()
    print(f"  Descarga regional correcta  ({lats.size} celdas)")


if __name__ == "__main__":
    print("1) Cálculos estadísticos")
    probar_estadistica()
    print("2) Datos de la NASA")
    try:
        probar_nasa()
    except Exception as e:  # noqa: BLE001
        print(f"  NO se pudo consultar a la NASA: {e}")
        sys.exit(1)
    print("\nTodo listo. Inicia la herramienta con:  streamlit run app.py")
