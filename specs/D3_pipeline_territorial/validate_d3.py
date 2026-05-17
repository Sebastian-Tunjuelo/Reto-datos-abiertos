"""
Script de validación para el pipeline D3 — Territorial (UPRA).
Ejecutar después de modules.territorial.ingestion (run_pipeline o __main__).

Uso:
    python specs/D3_pipeline_territorial/validate_d3.py

O desde Python:
    from specs.D3_pipeline_territorial.validate_d3 import run_validations
    run_validations()  # Lanza AssertionError si algo falla
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from shared.config import DATA_DIR
from shared.dane_codes import MVP_CODIGOS

# ---------------------------------------------------------------------------
# Constantes de validación
# ---------------------------------------------------------------------------

COLUMNAS_APTITUD = [
    "codigo_dane", "municipio", "departamento", "cultivo",
    "area_alta_ha", "area_media_ha", "area_baja_ha", "area_exclusion_ha",
    "area_total_ha", "pct_alta", "pct_media", "pct_baja", "pct_exclusion",
]

COLUMNAS_FRONTERA = [
    "codigo_dane", "municipio", "departamento",
    "area_condicionada_ha", "area_no_condicionada_ha",
    "area_total_ha", "pct_condicionada", "pct_no_condicionada",
]

TOLERANCIA_PCT = 0.001


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def run_validations(data_dir: Path = DATA_DIR) -> None:
    """
    Ejecuta todas las validaciones del pipeline D3.

    Lee los 4 archivos Parquet generados por D3.1, D3.2 y D3.3 y verifica
    que cumplen el contrato de datos del proyecto.

    Args:
        data_dir: Directorio donde se encuentran los Parquets.
                  Por defecto usa DATA_DIR de shared/config.py.

    Raises:
        AssertionError: Si cualquier criterio de aceptación falla.
                        El mensaje incluye el prefijo ❌ y descripción del problema.
    """

    # -----------------------------------------------------------------------
    # 1. Existencia de archivos
    # -----------------------------------------------------------------------
    for nombre in ["aptitud_cafe", "aptitud_cacao", "aptitud_maiz", "frontera"]:
        path = data_dir / f"{nombre}.parquet"
        assert path.exists(), f"❌ Archivo no encontrado: {path}"

    cafe  = pd.read_parquet(data_dir / "aptitud_cafe.parquet")
    cacao = pd.read_parquet(data_dir / "aptitud_cacao.parquet")
    maiz  = pd.read_parquet(data_dir / "aptitud_maiz.parquet")
    front = pd.read_parquet(data_dir / "frontera.parquet")

    print(f"  Archivos cargados: cafe={len(cafe)}, cacao={len(cacao)}, maiz={len(maiz)}, frontera={len(front)} filas")

    # -----------------------------------------------------------------------
    # 2. Esquema — columnas presentes
    # -----------------------------------------------------------------------
    for df, nombre in [(cafe, "aptitud_cafe"), (cacao, "aptitud_cacao"), (maiz, "aptitud_maiz")]:
        faltantes = set(COLUMNAS_APTITUD) - set(df.columns)
        assert not faltantes, (
            f"❌ {nombre}: columnas faltantes en el esquema: {sorted(faltantes)}"
        )

    faltantes_front = set(COLUMNAS_FRONTERA) - set(front.columns)
    assert not faltantes_front, (
        f"❌ frontera: columnas faltantes en el esquema: {sorted(faltantes_front)}"
    )

    # -----------------------------------------------------------------------
    # 3. codigo_dane — string de 5 dígitos exactos
    # -----------------------------------------------------------------------
    for df, nombre in [(cafe, "cafe"), (cacao, "cacao"), (maiz, "maiz"), (front, "frontera")]:
        mal_formato = df[df["codigo_dane"].str.len() != 5]["codigo_dane"].tolist()
        assert not mal_formato, (
            f"❌ {nombre}: codigo_dane con longitud != 5: {mal_formato}"
        )

    # -----------------------------------------------------------------------
    # 4. Columna cultivo
    # -----------------------------------------------------------------------
    assert (cafe["cultivo"] == "Café").all(), (
        f"❌ aptitud_cafe: cultivo contiene valores distintos de 'Café': "
        f"{cafe[cafe['cultivo'] != 'Café']['cultivo'].unique().tolist()}"
    )
    assert (cacao["cultivo"] == "Cacao").all(), (
        f"❌ aptitud_cacao: cultivo contiene valores distintos de 'Cacao': "
        f"{cacao[cacao['cultivo'] != 'Cacao']['cultivo'].unique().tolist()}"
    )
    assert (maiz["cultivo"] == "Maíz").all(), (
        f"❌ aptitud_maiz: cultivo contiene valores distintos de 'Maíz': "
        f"{maiz[maiz['cultivo'] != 'Maíz']['cultivo'].unique().tolist()}"
    )

    # -----------------------------------------------------------------------
    # 5. Tipos numéricos — float64
    # -----------------------------------------------------------------------
    cols_float_aptitud = [
        "area_alta_ha", "area_media_ha", "area_baja_ha", "area_exclusion_ha",
        "area_total_ha", "pct_alta", "pct_media", "pct_baja", "pct_exclusion",
    ]
    for df, nombre in [(cafe, "cafe"), (cacao, "cacao"), (maiz, "maiz")]:
        for col in cols_float_aptitud:
            assert df[col].dtype == "float64", (
                f"❌ {nombre}.{col}: se esperaba float64, se encontró {df[col].dtype}"
            )

    cols_float_front = [
        "area_condicionada_ha", "area_no_condicionada_ha",
        "area_total_ha", "pct_condicionada", "pct_no_condicionada",
    ]
    for col in cols_float_front:
        assert front[col].dtype == "float64", (
            f"❌ frontera.{col}: se esperaba float64, se encontró {front[col].dtype}"
        )

    # -----------------------------------------------------------------------
    # 6. area_total_ha > 0 en todos los registros
    # -----------------------------------------------------------------------
    for df, nombre in [(cafe, "cafe"), (cacao, "cacao"), (maiz, "maiz"), (front, "frontera")]:
        cero_o_neg = df[df["area_total_ha"] <= 0]["codigo_dane"].tolist()
        assert not cero_o_neg, (
            f"❌ {nombre}: registros con area_total_ha <= 0 en municipios: {cero_o_neg}"
        )

    # -----------------------------------------------------------------------
    # 7. Porcentajes en rango [0.0, 1.0]
    # -----------------------------------------------------------------------
    for df, nombre in [(cafe, "cafe"), (cacao, "cacao"), (maiz, "maiz")]:
        for col in ["pct_alta", "pct_media", "pct_baja", "pct_exclusion"]:
            fuera = df[(df[col] < 0) | (df[col] > 1)]["codigo_dane"].tolist()
            assert not fuera, (
                f"❌ {nombre}.{col}: valores fuera de [0, 1] en municipios: {fuera}"
            )

    for col in ["pct_condicionada", "pct_no_condicionada"]:
        fuera = front[(front[col] < 0) | (front[col] > 1)]["codigo_dane"].tolist()
        assert not fuera, (
            f"❌ frontera.{col}: valores fuera de [0, 1] en municipios: {fuera}"
        )

    # -----------------------------------------------------------------------
    # 8. Suma de porcentajes ≈ 1.0 (tolerancia ±0.001)
    # -----------------------------------------------------------------------
    for df, nombre in [(cafe, "cafe"), (cacao, "cacao"), (maiz, "maiz")]:
        suma = df[["pct_alta", "pct_media", "pct_baja", "pct_exclusion"]].sum(axis=1)
        fuera = df[(suma - 1.0).abs() > TOLERANCIA_PCT]
        assert fuera.empty, (
            f"❌ {nombre}: porcentajes no suman 1.0 (±{TOLERANCIA_PCT}) "
            f"en municipios: {fuera['codigo_dane'].tolist()} "
            f"(sumas: {suma[fuera.index].round(4).tolist()})"
        )

    suma_front = front[["pct_condicionada", "pct_no_condicionada"]].sum(axis=1)
    fuera_front = front[(suma_front - 1.0).abs() > TOLERANCIA_PCT]
    assert fuera_front.empty, (
        f"❌ frontera: porcentajes no suman 1.0 (±{TOLERANCIA_PCT}) "
        f"en municipios: {fuera_front['codigo_dane'].tolist()} "
        f"(sumas: {suma_front[fuera_front.index].round(4).tolist()})"
    )

    # -----------------------------------------------------------------------
    # 9. Cobertura MVP — los 15 municipios presentes
    # -----------------------------------------------------------------------
    for df, nombre in [(cafe, "cafe"), (cacao, "cacao"), (maiz, "maiz"), (front, "frontera")]:
        presentes = set(df["codigo_dane"].unique())
        faltantes_mvp = set(MVP_CODIGOS) - presentes
        assert not faltantes_mvp, (
            f"❌ {nombre}: municipios del MVP sin datos: {sorted(faltantes_mvp)}"
        )
        n_unicos = df["codigo_dane"].nunique()
        assert n_unicos == 15, (
            f"❌ {nombre}: se esperaban exactamente 15 municipios únicos, "
            f"se encontraron {n_unicos}"
        )

    # -----------------------------------------------------------------------
    # 10. Sin duplicados por codigo_dane
    # -----------------------------------------------------------------------
    for df, nombre in [(cafe, "cafe"), (cacao, "cacao"), (maiz, "maiz"), (front, "frontera")]:
        dups = df[df.duplicated("codigo_dane", keep=False)]["codigo_dane"].tolist()
        assert not dups, (
            f"❌ {nombre}: duplicados por codigo_dane: {dups}"
        )

    # -----------------------------------------------------------------------
    # Resumen final
    # -----------------------------------------------------------------------
    print("\n✅ Todos los criterios de aceptación pasaron\n")
    print("=" * 55)
    print("Resumen D3 — Pipeline Territorial")
    print("=" * 55)

    for df, nombre, cultivo_val in [
        (cafe,  "aptitud_cafe",  "Café"),
        (cacao, "aptitud_cacao", "Cacao"),
        (maiz,  "aptitud_maiz",  "Maíz"),
    ]:
        print(f"\n  {nombre} ({cultivo_val}) — {len(df)} municipios")
        print(f"    pct_alta   media: {df['pct_alta'].mean():.1%}  "
              f"min: {df['pct_alta'].min():.1%}  max: {df['pct_alta'].max():.1%}")
        print(f"    pct_media  media: {df['pct_media'].mean():.1%}  "
              f"min: {df['pct_media'].min():.1%}  max: {df['pct_media'].max():.1%}")
        print(f"    pct_baja   media: {df['pct_baja'].mean():.1%}  "
              f"min: {df['pct_baja'].min():.1%}  max: {df['pct_baja'].max():.1%}")
        print(f"    pct_excl   media: {df['pct_exclusion'].mean():.1%}  "
              f"min: {df['pct_exclusion'].min():.1%}  max: {df['pct_exclusion'].max():.1%}")

    print(f"\n  frontera — {len(front)} municipios")
    print(f"    pct_condicionada    media: {front['pct_condicionada'].mean():.1%}  "
          f"min: {front['pct_condicionada'].min():.1%}  max: {front['pct_condicionada'].max():.1%}")
    print(f"    pct_no_condicionada media: {front['pct_no_condicionada'].mean():.1%}  "
          f"min: {front['pct_no_condicionada'].min():.1%}  max: {front['pct_no_condicionada'].max():.1%}")
    print()


if __name__ == "__main__":
    run_validations()
