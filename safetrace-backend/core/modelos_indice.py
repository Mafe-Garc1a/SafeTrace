"""Modelos matemáticos del índice de priorización (RF-66, RF-67).

Funciones puras, sin base de datos: reciben números y devuelven números. Las usa app/crud/ia_indice.py.
Fuente: «SafeTrace: modelos matemáticos del índice de priorización» (docs/).

Son simplificaciones para ordenar revisiones, no un análisis estructural (RNF-33, RNF-36):
- Vibración libre (EDO lineal homogénea de 2.º orden): periodo del edificio y curva x(t).
- Resonancia (EDO lineal no homogénea de 2.º orden): factor de amplificación F → variable x₃.
- Atenuación (ecuación de onda, simetría esférica): distancia al foco R → variable x₅.
- Crecimiento de fisura (EDO de 1.er orden): tasa k. Solo informativa; no entra en el índice.
"""

import math
from datetime import datetime

DIAS_POR_MES = 30.4375  # 365,25 / 12
CERCANIA_REFERENCIA_KM = 20  # x₅ = 20 / R: a 20 km o menos del foco vale 1
FACTOR_MAXIMO = 5  # x₃ = F / 5

# --- Ecuaciones -----------------------------------------------------------------


def periodo_natural(numero_pisos: int) -> float:
    """T ≈ 0,1·N segundos. Aproximación general para priorizar, no para diseñar."""
    return 0.1 * numero_pisos


def frecuencias(periodo_s: float, zeta: float) -> tuple[float, float]:
    """ωₙ = 2π/T y ωd = ωₙ·√(1 − ζ²), en rad/s."""
    omega_n = 2 * math.pi / periodo_s
    return omega_n, omega_n * math.sqrt(1 - zeta**2)


def respuesta_libre(periodo_s: float, zeta: float, t: float) -> float:
    """Solución de m·x'' + c·x' + k·x = 0 con x(0) = 1 y x'(0) = 0 (ζ < 1)."""
    omega_n, omega_d = frecuencias(periodo_s, zeta)
    b = zeta * omega_n / omega_d  # sale de imponer x'(0) = 0
    return math.exp(-zeta * omega_n * t) * (math.cos(omega_d * t) + b * math.sin(omega_d * t))


def factor_resonancia(r: float, zeta: float) -> float:
    """F = 1 / √((1 − r²)² + (2ζr)²), con r = T / Tₛ."""
    return 1 / math.sqrt((1 - r**2) ** 2 + (2 * zeta * r) ** 2)


def distancia_hipocentral(distancia_epicentral_km: float, profundidad_km: float) -> float:
    """R = √(d² + h²)."""
    return math.hypot(distancia_epicentral_km, profundidad_km)


def cercania(distancia_hipocentral_km: float) -> float:
    """Amplitud relativa de la onda, que cae como 1/R. Vale 1 dentro de los primeros 20 km."""
    if distancia_hipocentral_km <= CERCANIA_REFERENCIA_KM:
        return 1.0
    return CERCANIA_REFERENCIA_KM / distancia_hipocentral_km


def tasa_crecimiento(ancho_1_mm: float, ancho_2_mm: float, meses: float) -> float:
    """k = ln(D₂/D₁)/Δt, por mes, de dD/dt = k·D. Solo informativa (RNF-33)."""
    if ancho_1_mm <= 0 or ancho_2_mm <= 0 or meses <= 0:
        raise ValueError("Se necesitan dos anchos positivos y un tiempo mayor que cero")
    return math.log(ancho_2_mm / ancho_1_mm) / meses


# --- Índice -------------------------------------------------------------------------


def _entre_0_y_1(valor: float) -> float:
    return min(1.0, max(0.0, valor))


def meses_entre(desde: datetime | None, hasta: datetime) -> float | None:
    if desde is None:
        return None
    return max(0.0, (hasta - desde).total_seconds() / 86400 / DIAS_POR_MES)


def derivadas(numero_pisos: int, distancia_km: float, profundidad_km: float, parametros: dict) -> dict:
    """Resultados de los modelos que alimentan el índice: periodo, F y R."""
    periodo = periodo_natural(numero_pisos)
    r = periodo / parametros["periodo_suelo_s"]
    return {
        "periodo_s": round(periodo, 3),
        "relacion_periodos": round(r, 3),
        "factor_resonancia": round(factor_resonancia(r, parametros["zeta"]), 3),
        "distancia_hipocentral_km": round(distancia_hipocentral(distancia_km, profundidad_km), 1),
    }


def normalizar(variables: dict, parametros: dict, momento: datetime) -> dict:
    """Lleva las ocho variables de RF-67 a una escala de 0 a 1.

    `variables` debe traer también periodo_s, factor_resonancia y distancia_hipocentral_km (ver `derivadas`).
    Sin revisión registrada, x₈ vale 1: es lo que más tiempo lleva sin revisarse.
    """
    meses = meses_entre(variables["fecha_ultima_revision"], momento)
    valores_sistema = parametros["valores_sistema_constructivo"]
    return {
        "antiguedad": _entre_0_y_1((momento.year - variables["anio_construccion"]) / 100),
        "sistema_constructivo": _entre_0_y_1(
            valores_sistema.get(variables["sistema_constructivo"], valores_sistema["OTRO"])
        ),
        "resonancia": _entre_0_y_1(variables["factor_resonancia"] / FACTOR_MAXIMO),
        "magnitud": _entre_0_y_1((variables["magnitud"] - 5) / 3),
        "cercania_foco": _entre_0_y_1(cercania(variables["distancia_hipocentral_km"])),
        "antecedentes_danos": _entre_0_y_1(variables["antecedentes_danos"] / 5),
        "falta_mantenimiento": _entre_0_y_1(1 - variables["antecedentes_mantenimiento"] / 5),
        "tiempo_sin_revision": 1.0 if meses is None else _entre_0_y_1(meses / 24),
    }


def indice(normalizadas: dict, pesos: dict) -> tuple[float, dict]:
    """I = 100·Σ wᵢ·xᵢ. Los pesos se dividen por su suma, así el índice siempre queda entre 0 y 100."""
    if set(pesos) != set(normalizadas):
        raise ValueError(f"Los pesos deben ser exactamente estas variables: {sorted(normalizadas)}")
    if any(p < 0 for p in pesos.values()) or sum(pesos.values()) <= 0:
        raise ValueError("Los pesos no pueden ser negativos y deben sumar más que cero")
    total = sum(pesos.values())
    aportes = {k: round(100 * pesos[k] / total * normalizadas[k], 2) for k in normalizadas}
    valor = 100 * sum(pesos[k] / total * normalizadas[k] for k in normalizadas)
    return round(_entre_0_y_1(valor / 100) * 100, 2), aportes


# --- Puntos de las gráficas (se calculan al pedirlos, no se guardan) -----------------


def curva_vibracion(periodo_s: float, zeta: float, puntos: int = 101) -> list[dict]:
    duracion = 10 * periodo_s
    return [
        {"t": round(t, 4), "x": round(respuesta_libre(periodo_s, zeta, t), 4)}
        for t in (duracion * i / (puntos - 1) for i in range(puntos))
    ]


def curva_resonancia(zeta: float, r_maximo: float = 3, puntos: int = 121) -> list[dict]:
    return [
        {"r": round(r, 4), "factor": round(factor_resonancia(r, zeta), 4)}
        for r in (r_maximo * i / (puntos - 1) for i in range(puntos))
    ]


def curva_atenuacion(profundidad_km: float, distancia_maxima_km: float, puntos: int = 101) -> list[dict]:
    return [
        {
            "distancia_epicentral_km": round(d, 2),
            "distancia_hipocentral_km": round(distancia_hipocentral(d, profundidad_km), 2),
            "amplitud_relativa": round(cercania(distancia_hipocentral(d, profundidad_km)), 4),
        }
        for d in (distancia_maxima_km * i / (puntos - 1) for i in range(puntos))
    ]
