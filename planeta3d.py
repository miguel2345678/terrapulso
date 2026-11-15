"""
planeta3d.py
============
Prepara el globo 3D (planeta/planeta-tierra.html) para mostrarlo dentro de TerraPulso.

El globo es una ilustración hecha por el equipo con HTML, CSS y JavaScript (WebGL).
No usa librerías externas ni internet. Aquí solo se le pasan tres datos de la sesión:
el lugar analizado, su temperatura media según NASA POWER y los dos satélites (Terra y
Aqua) de donde provienen los datos de radiación y nubes.

AI disclosure / Uso de IA: this code was generated with AI assistance
(Claude, by Anthropic) and was run and verified by Team UCC.
"""
from __future__ import annotations

import json
from pathlib import Path

_AQUI = Path(__file__).parent
# Se acepta el archivo dentro de la carpeta planeta/ o suelto junto a app.py
RUTA = next((r for r in (_AQUI / "planeta" / "planeta-tierra.html", _AQUI / "planeta-tierra.html") if r.exists()),
            _AQUI / "planeta" / "planeta-tierra.html")

_SATELITES_CERES = """{ n: 'Terra', full: 'Terra', who: 'NASA', y: 1999, alt: 705, inc: 98.2, raan: 80, ph: 2.6, c: '#ffe08a',
      d: 'Lleva el instrumento CERES, que mide la energía que llega del Sol y la que devuelve la Tierra. De aquí salen datos de radiación y nubes que usa TerraPulso.' },
    { n: 'Aqua', full: 'Aqua', who: 'NASA', y: 2002, alt: 705, inc: 98.2, raan: 260, ph: 4.6, c: '#8ad8ff',
      d: 'También lleva CERES. Junto con Terra aporta las mediciones de radiación solar y cobertura de nubes que analiza TerraPulso.' },
    """


def disponible() -> bool:
    return RUTA.exists()


def html_del_planeta(lat: float, lon: float, nombre: str, detalle: str,
                     temperatura: float | None, en_colombia: bool) -> str:
    """Devuelve el HTML del globo centrado en el lugar analizado."""
    h = RUTA.read_text(encoding="utf-8")

    # 1) Que el globo abra mirando hacia el lugar analizado
    h = h.replace("function home() { return mul(Rx(8 * D), Ry(80 * D)); }",
                  f"function home() {{ return mul(Rx({lat:.3f} * D), Ry({-lon:.3f} * D)); }}", 1)

    # 2) Fuera de Colombia se muestran todos los países
    if not en_colombia:
        h = h.replace('var SOLO_PAIS = "Colombia";', "var SOLO_PAIS = null;", 1)

    # 3) El lugar analizado aparece como ciudad, con su temperatura media de NASA POWER
    temp_js = "null" if temperatura is None else f"{temperatura:.2f}"
    ciudad = (f"var TEMPS = {{}}; try {{ CITIES = CITIES.filter(function (c) {{ return Math.abs(c.lat - ({lat:.3f})) > 0.4 || "
              f"Math.abs(c.lon - ({lon:.3f})) > 0.4; }}); CITIES.push(mkCity([{json.dumps(detalle)}, {json.dumps(nombre)}, "
              f"{lat:.3f}, {lon:.3f}, {temp_js}])); }} catch (errTP) {{}}")
    h = h.replace("var TEMPS = {};", ciudad, 1)

    # 4) Terra y Aqua: los satélites de donde vienen los datos de radiación y nubes
    if "n: 'Terra'" not in h:
        h = h.replace("{ n: 'SWOT'", _SATELITES_CERES + "{ n: 'SWOT'", 1)
    return h
