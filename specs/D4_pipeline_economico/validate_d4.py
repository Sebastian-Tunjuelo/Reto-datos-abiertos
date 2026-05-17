"""
Script de validacion para el pipeline D4 — Economico (Agroinsumos).
Ejecutar despues de modules.economic.ingestion.run_pipeline().
"""
import sys
from pathlib import Path

import pandas as pd

try:
    from scipy.stats import percentileofscore
except Exception:
    percentileofscore = None

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from shared.config import DATA_DIR

COLUMNAS_MENSUAL = [
    "fecha",
    "año",
    "mes",
    "indice_total",
    "fertilizantes",
    "plaguicidas",
    "urea",
    "dap",
    "kcl",
]

COLUMNAS_ANUAL = [
    "año",
    "indice_total",
    "fertilizantes",
    "plaguicidas",
    "urea",
    "dap",
    "kcl",
    "n_meses",
    "pct_fertilizantes",
    "pct_indice_total",
    "señal_riesgo",
]

SEÑALES_VALIDAS = {"Bajo", "Medio", "Alto"}


def _percentil_rank(serie: pd.Series, valor: float) -> float | None:
    serie = serie.dropna().astype(float)
    if len(serie) < 3:
        return None
    if percentileofscore is not None:
        return percentileofscore(serie, valor, kind="rank") / 100
    ordenados = serie.sort_values().to_numpy()
    leq = (ordenados <= valor).sum()
    return leq / len(ordenados)


def run_validations(data_dir: Path = DATA_DIR) -> None:
    """Ejecuta todas las validaciones. Lanza AssertionError si alguna falla."""
    for nombre in ["agroinsumos_mensual", "agroinsumos"]:
        path = data_dir / f"{nombre}.parquet"
        assert path.exists(), f"❌ Archivo no encontrado: {path}"

    mensual = pd.read_parquet(data_dir / "agroinsumos_mensual.parquet")
    anual = pd.read_parquet(data_dir / "agroinsumos.parquet")

    faltantes_m = set(COLUMNAS_MENSUAL) - set(mensual.columns)
    assert not faltantes_m, f"❌ agroinsumos_mensual: columnas faltantes: {faltantes_m}"

    patron_fecha = mensual["fecha"].astype(str).str.match(r"^\d{4}-\d{2}$")
    assert patron_fecha.all(), (
        f"❌ agroinsumos_mensual: {(~patron_fecha).sum()} fechas con formato incorrecto"
    )

    assert mensual["año"].dtype in ("int64", "Int64"), (
        f"❌ agroinsumos_mensual.año no es int64/Int64: {mensual['año'].dtype}"
    )
    assert mensual["mes"].dtype in ("int64", "Int64"), (
        f"❌ agroinsumos_mensual.mes no es int64/Int64: {mensual['mes'].dtype}"
    )
    for col in ["indice_total", "fertilizantes", "plaguicidas", "urea", "dap", "kcl"]:
        assert mensual[col].dtype == "float64", (
            f"❌ agroinsumos_mensual.{col} no es float64: {mensual[col].dtype}"
        )

    años_m = mensual["año"].dropna()
    assert años_m.between(2007, 2024).all(), (
        "❌ agroinsumos_mensual: años fuera de rango 2007-2024: "
        f"{años_m[~años_m.between(2007, 2024)].unique().tolist()}"
    )
    meses_m = mensual["mes"].dropna()
    assert meses_m.between(1, 12).all(), (
        "❌ agroinsumos_mensual: meses fuera de rango 1-12: "
        f"{meses_m[~meses_m.between(1, 12)].unique().tolist()}"
    )

    dups_m = mensual.duplicated(["año", "mes"]).sum()
    assert dups_m == 0, f"❌ agroinsumos_mensual: {dups_m} duplicados por (año, mes)"

    mensual_sorted = mensual.sort_values(["año", "mes"])
    assert mensual.reset_index(drop=True).equals(mensual_sorted.reset_index(drop=True)), (
        "❌ agroinsumos_mensual: no esta ordenado por (año, mes)"
    )

    assert len(mensual) >= 60, (
        f"❌ agroinsumos_mensual: solo {len(mensual)} registros — se esperan ≥ 60 (>= 5 años)"
    )

    faltantes_a = set(COLUMNAS_ANUAL) - set(anual.columns)
    assert not faltantes_a, f"❌ agroinsumos: columnas faltantes: {faltantes_a}"

    assert anual["año"].dtype == "int64", (
        f"❌ agroinsumos.año no es int64: {anual['año'].dtype}"
    )
    assert anual["n_meses"].dtype == "int64", (
        f"❌ agroinsumos.n_meses no es int64: {anual['n_meses'].dtype}"
    )
    for col in [
        "indice_total",
        "fertilizantes",
        "plaguicidas",
        "urea",
        "dap",
        "kcl",
        "pct_fertilizantes",
        "pct_indice_total",
    ]:
        assert anual[col].dtype == "float64", (
            f"❌ agroinsumos.{col} no es float64: {anual[col].dtype}"
        )

    años_a = anual["año"]
    assert años_a.between(2007, 2024).all(), (
        "❌ agroinsumos: años fuera de rango 2007-2024: "
        f"{años_a[~años_a.between(2007, 2024)].tolist()}"
    )
    assert anual["n_meses"].between(1, 12).all(), (
        "❌ agroinsumos: n_meses fuera de rango 1-12"
    )

    for col in ["pct_fertilizantes", "pct_indice_total"]:
        vals = anual[col].dropna()
        fuera = vals[(vals < 0) | (vals > 1)]
        assert fuera.empty, (
            f"❌ agroinsumos.{col}: valores fuera de [0.0, 1.0]: {fuera.tolist()}"
        )

    señales_reales = set(anual["señal_riesgo"].unique())
    invalidas = señales_reales - SEÑALES_VALIDAS
    assert not invalidas, (
        f"❌ agroinsumos.señal_riesgo: valores invalidos: {invalidas}"
    )
    assert anual["señal_riesgo"].notna().all(), "❌ agroinsumos.señal_riesgo: hay nulos"

    dups_a = anual.duplicated("año").sum()
    assert dups_a == 0, f"❌ agroinsumos: {dups_a} duplicados por año"

    assert (anual["año"].diff().dropna() > 0).all(), (
        "❌ agroinsumos: no esta ordenado por año ascendente"
    )

    assert anual["año"].nunique() >= 6, (
        f"❌ agroinsumos: solo {anual['año'].nunique()} años — se esperan ≥ 6"
    )

    año_min = anual["año"].min()
    primeros_2 = anual[anual["año"] <= año_min + 1]
    assert primeros_2["pct_fertilizantes"].isna().all(), (
        "❌ agroinsumos: los primeros 2 años deberian tener pct_fertilizantes=NaN "
        f"(años {año_min} y {año_min + 1})"
    )
    assert primeros_2["pct_indice_total"].isna().all(), (
        "❌ agroinsumos: los primeros 2 años deberian tener pct_indice_total=NaN"
    )

    años_con_historia = anual[anual["año"] > año_min + 2]
    años_con_historia = años_con_historia[años_con_historia["fertilizantes"].notna()]
    nulos_pct = años_con_historia["pct_fertilizantes"].isna().sum()
    assert nulos_pct == 0, (
        "❌ agroinsumos: "
        f"{nulos_pct} años con historia suficiente tienen pct_fertilizantes=NaN"
    )

    años_mensual = set(mensual["año"].dropna().unique())
    años_anual = set(anual["año"].unique())
    extra = años_anual - años_mensual
    assert not extra, (
        f"❌ agroinsumos: años en anual que no estan en mensual: {extra}"
    )

    conteo_mensual = mensual.groupby("año")["mes"].count().rename("n_meses_real")
    merged = anual.set_index("año").join(conteo_mensual, how="left")
    discrepancias = merged[merged["n_meses"] != merged["n_meses_real"]]
    assert discrepancias.empty, (
        "❌ agroinsumos: n_meses no coincide con conteo mensual en años: "
        f"{discrepancias.index.tolist()}"
    )

    anual_valid = anual.dropna(subset=["fertilizantes", "pct_fertilizantes"])
    verificados = 0
    for _, row in anual_valid.iterrows():
        año = int(row["año"])
        historico = anual[anual["año"] < año]
        esperado = _percentil_rank(historico["fertilizantes"], float(row["fertilizantes"]))
        if esperado is None:
            continue
        actual = float(row["pct_fertilizantes"])
        assert abs(actual - esperado) <= 0.02, (
            "❌ agroinsumos: pct_fertilizantes no coincide con recomputo historico "
            f"para año {año} (actual={actual:.3f}, esperado={esperado:.3f})"
        )
        verificados += 1
        if verificados >= 3:
            break

    print("OK: Todos los criterios de aceptacion pasaron")
    print("\nResumen:")
    print(
        f"  agroinsumos_mensual: {len(mensual):>5} registros | "
        f"años {int(mensual['año'].min())}-{int(mensual['año'].max())}"
    )
    print(
        f"  agroinsumos anual:   {len(anual):>5} años     | "
        f"años {int(anual['año'].min())}-{int(anual['año'].max())}"
    )
    print(f"\n  n_meses promedio: {anual['n_meses'].mean():.1f}")
    print(
        "  Años con datos incompletos (n_meses < 12): "
        f"{(anual['n_meses'] < 12).sum()}"
    )
    print("\n  Distribucion señal_riesgo:")
    for señal in ["Bajo", "Medio", "Alto"]:
        n = (anual["señal_riesgo"] == señal).sum()
        print(f"    {señal:5s}: {n:>3} años ({n / len(anual):.0%})")
    print(
        f"\n  indice_total  - min: {anual['indice_total'].min():.1f} | "
        f"max: {anual['indice_total'].max():.1f} | "
        f"media: {anual['indice_total'].mean():.1f}"
    )
    print(
        f"  fertilizantes - min: {anual['fertilizantes'].min():.1f} | "
        f"max: {anual['fertilizantes'].max():.1f} | "
        f"media: {anual['fertilizantes'].mean():.1f}"
    )
    print(
        "\n  Percentiles calculados para "
        f"{anual['pct_fertilizantes'].notna().sum()} de {len(anual)} años"
    )


if __name__ == "__main__":
    run_validations()
