"""
Script de validación para el pipeline D1 — EVA.
Ejecutar después de modules.agricultural.ingestion.run_pipeline()

Uso:
    python specs/D1_pipeline_eva/validate_d1.py

O desde Python:
    from specs.D1_pipeline_eva.validate_d1 import run_validations
    run_validations()
"""
import sys
from pathlib import Path

import pandas as pd

# Ajustar path para importar desde la raíz del proyecto
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from shared.config import DATA_DIR, RENDIMIENTO_RANGOS
from shared.dane_codes import MVP_CODIGOS

CULTIVOS_ESPERADOS = {"Café", "Cacao", "Maíz"}
CICLOS_VALIDOS = {"PERMANENTE", "TRANSITORIO"}

COLUMNAS_ESPERADAS = [
    "codigo_dane", "municipio", "departamento", "cultivo",
    "año", "periodo", "rendimiento", "area_sembrada",
    "area_cosechada", "produccion", "ciclo", "fuente",
]


def run_validations(data_dir: Path = DATA_DIR) -> None:
    """Ejecuta todas las validaciones. Lanza AssertionError si alguna falla."""

    # ------------------------------------------------------------------ #
    # 1. Existencia de archivos                                            #
    # ------------------------------------------------------------------ #
    for nombre in ["eva_historica", "eva_reciente", "eva_completa"]:
        path = data_dir / f"{nombre}.parquet"
        assert path.exists(), (
            f"❌ Archivo no encontrado: {path}. "
            f"Ejecuta primero: python -m modules.agricultural.ingestion"
        )

    hist = pd.read_parquet(data_dir / "eva_historica.parquet")
    rec  = pd.read_parquet(data_dir / "eva_reciente.parquet")
    comp = pd.read_parquet(data_dir / "eva_completa.parquet")

    # ------------------------------------------------------------------ #
    # 2. Integridad de la unión                                            #
    # ------------------------------------------------------------------ #
    assert len(comp) == len(hist) + len(rec), (
        f"❌ Integridad de unión: eva_completa tiene {len(comp)} filas, "
        f"pero eva_historica ({len(hist)}) + eva_reciente ({len(rec)}) = {len(hist) + len(rec)}. "
        f"Hay filas perdidas o duplicadas en la concatenación."
    )

    assert hist["año"].max() <= 2018, (
        f"❌ eva_historica contiene años > 2018: máximo encontrado = {hist['año'].max()}. "
        f"El dataset histórico solo debe cubrir 2007–2018."
    )

    assert rec["año"].min() >= 2019, (
        f"❌ eva_reciente contiene años < 2019: mínimo encontrado = {rec['año'].min()}. "
        f"El dataset reciente solo debe cubrir 2019–2024."
    )

    # ------------------------------------------------------------------ #
    # 3. Esquema — columnas presentes en los 3 archivos                   #
    # ------------------------------------------------------------------ #
    for df, nombre in [(hist, "eva_historica"), (rec, "eva_reciente"), (comp, "eva_completa")]:
        faltantes = set(COLUMNAS_ESPERADAS) - set(df.columns)
        assert not faltantes, (
            f"❌ {nombre}: columnas faltantes en el esquema unificado: {sorted(faltantes)}. "
            f"Columnas presentes: {sorted(df.columns.tolist())}"
        )

    # ------------------------------------------------------------------ #
    # 4. Tipos de datos                                                    #
    # ------------------------------------------------------------------ #
    longitudes_invalidas = comp["codigo_dane"].str.len().ne(5).sum()
    assert longitudes_invalidas == 0, (
        f"❌ codigo_dane: {longitudes_invalidas} registros con longitud != 5. "
        f"Todos los códigos DANE deben tener exactamente 5 dígitos (con cero inicial)."
    )

    assert comp["año"].dtype in ("int64", "Int64"), (
        f"❌ año no es int64/Int64: dtype actual = {comp['año'].dtype}. "
        f"Usar pd.to_numeric(...).astype('Int64') en el pipeline."
    )

    assert comp["rendimiento"].dtype == "float64", (
        f"❌ rendimiento no es float64: dtype actual = {comp['rendimiento'].dtype}."
    )

    for col in ["area_sembrada", "area_cosechada", "produccion"]:
        assert comp[col].dtype == "float64", (
            f"❌ {col} no es float64: dtype actual = {comp[col].dtype}."
        )

    # ------------------------------------------------------------------ #
    # 5. Valores de dominio                                                #
    # ------------------------------------------------------------------ #
    cultivos_reales = set(comp["cultivo"].dropna().unique())
    inesperados = cultivos_reales - CULTIVOS_ESPERADOS
    assert not inesperados, (
        f"❌ Cultivos inesperados en eva_completa: {inesperados}. "
        f"Solo se permiten: {CULTIVOS_ESPERADOS}"
    )

    ciclos_reales = set(comp["ciclo"].dropna().unique())
    ciclos_invalidos = ciclos_reales - CICLOS_VALIDOS
    assert not ciclos_invalidos, (
        f"❌ Valores de ciclo inválidos: {ciclos_invalidos}. "
        f"Solo se permiten: {CICLOS_VALIDOS} (o NaN)."
    )

    n_cero = (comp["rendimiento"] == 0.0).sum()
    assert n_cero == 0, (
        f"❌ {n_cero} registros con rendimiento == 0.0. "
        f"Los rendimientos nulos o inválidos deben convertirse a NaN, no a 0."
    )

    for cultivo, (rmin, rmax) in RENDIMIENTO_RANGOS.items():
        sub = comp[comp["cultivo"] == cultivo]["rendimiento"].dropna()
        fuera = sub[(sub < rmin) | (sub > rmax)]
        assert fuera.empty, (
            f"❌ {cultivo}: {len(fuera)} rendimientos fuera del rango válido [{rmin}, {rmax}] t/ha. "
            f"Valores extremos: min={fuera.min():.3f}, max={fuera.max():.3f}. "
            f"Revisar la limpieza en ingestion.py."
        )

    # ------------------------------------------------------------------ #
    # 6. Cobertura del MVP                                                 #
    # ------------------------------------------------------------------ #
    codigos_presentes = set(comp["codigo_dane"].unique())
    faltantes_mvp = set(MVP_CODIGOS) - codigos_presentes
    assert not faltantes_mvp, (
        f"❌ Municipios del MVP sin ningún registro en eva_completa: {faltantes_mvp}. "
        f"Verificar que el pipeline descargó datos para todos los 15 municipios."
    )

    n_municipios = comp["codigo_dane"].nunique()
    assert n_municipios == 15, (
        f"❌ Se esperaban exactamente 15 municipios únicos, se encontraron {n_municipios}. "
        f"Códigos presentes: {sorted(codigos_presentes)}"
    )

    # ------------------------------------------------------------------ #
    # 7. Columna fuente                                                    #
    # ------------------------------------------------------------------ #
    fuentes_hist = set(hist["fuente"].unique())
    assert fuentes_hist == {"historica"}, (
        f"❌ eva_historica tiene valores de fuente distintos a 'historica': {fuentes_hist}."
    )

    fuentes_rec = set(rec["fuente"].unique())
    assert fuentes_rec == {"reciente"}, (
        f"❌ eva_reciente tiene valores de fuente distintos a 'reciente': {fuentes_rec}."
    )

    # ------------------------------------------------------------------ #
    # 8. Duplicados                                                        #
    # ------------------------------------------------------------------ #
    llave = ["codigo_dane", "cultivo", "año", "periodo", "fuente"]
    for df, nombre in [(hist, "eva_historica"), (rec, "eva_reciente"), (comp, "eva_completa")]:
        n_dups = df.duplicated(subset=llave).sum()
        assert n_dups == 0, (
            f"❌ {nombre}: {n_dups} filas duplicadas por clave {llave}. "
            f"El pipeline debe deduplicar antes de guardar."
        )

    # ------------------------------------------------------------------ #
    # Resumen final                                                        #
    # ------------------------------------------------------------------ #
    print("✅ Todos los criterios de aceptación pasaron\n")
    print("Resumen:")
    print(f"  EVA histórica:  {len(hist):>6,} registros | años {hist['año'].min()}–{hist['año'].max()}")
    print(f"  EVA reciente:   {len(rec):>6,} registros | años {rec['año'].min()}–{rec['año'].max()}")
    print(f"  EVA completa:   {len(comp):>6,} registros | años {comp['año'].min()}–{comp['año'].max()}")
    print(f"\n  Municipios: {comp['codigo_dane'].nunique()}/15")
    print(
        f"  Registros con rendimiento=NaN: {comp['rendimiento'].isna().sum()} "
        f"({comp['rendimiento'].isna().mean():.1%})"
    )
    print()
    for cultivo in ["Café", "Cacao", "Maíz"]:
        mask = comp["cultivo"] == cultivo
        n = mask.sum()
        med = comp.loc[mask, "rendimiento"].mean()
        print(f"  {cultivo:<6}: {n:>5,} registros | rendimiento medio: {med:.2f} t/ha")


if __name__ == "__main__":
    run_validations()
