"""Validación de M4 - Explicabilidad SHAP y Narrativas."""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
import xgboost as xgb

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import CULTIVOS_MVP, DATA_DIR, MODELS_DIR

FEATURE_MATRIX_PATH = DATA_DIR / "feature_matrix.parquet"
EXPLICACION_PATH = DATA_DIR / "predicciones_con_explicacion.parquet"

CULTIVO_SLUGS = {
    "Café": "cafe",
    "Cacao": "cacao",
    "Maíz": "maiz",
}

EXPLAINER_PATHS = {
    cultivo: MODELS_DIR / f"shap_explainer_{slug}.pkl"
    for cultivo, slug in CULTIVO_SLUGS.items()
}

MODEL_PATHS = {
    cultivo: [
        MODELS_DIR / f"xgb_classifier_{slug}.pkl",
        MODELS_DIR / f"xgb_classifier_{slug}_model.pkl",
    ]
    for cultivo, slug in CULTIVO_SLUGS.items()
}

META_PATHS = {
    cultivo: MODELS_DIR / f"xgb_classifier_{slug}_meta.json"
    for cultivo, slug in CULTIVO_SLUGS.items()
}

OUTPUT_COLUMNS = {
    "codigo_dane",
    "año",
    "cultivo",
    "prediccion_riesgo",
    "narrativa_riesgo",
    "rendimiento_esperado",   # nuevo
    "etiqueta_riesgo",        # nuevo
}


def _find_existing_path(candidates: list[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    expected = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"M4: no se encontró ninguno de estos archivos esperados: {expected}")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_explainer(path: Path) -> shap.TreeExplainer:
    with path.open("rb") as handle:
        explainer = pickle.load(handle)
    assert hasattr(explainer, "shap_values"), f"M4: el explainer no expone shap_values: {path}"
    assert hasattr(explainer, "expected_value"), f"M4: el explainer no expone expected_value: {path}"
    return explainer


def _load_model(path: Path) -> Any:
    model = joblib.load(path)
    assert hasattr(model, "predict"), f"M4: el modelo no expone predict: {path}"
    assert hasattr(model, "predict_proba"), f"M4: el modelo no expone predict_proba: {path}"
    return model


def _select_positive_class_value(value: Any) -> float:
    if isinstance(value, (list, tuple, np.ndarray)):
        value_array = np.asarray(value).reshape(-1)
        if value_array.size == 0:
            raise ValueError("M4: expected_value vacío en el explainer")
        if value_array.size > 1:
            return float(value_array[1])
        return float(value_array[0])
    return float(value)


def _normalize_shap_output(
    shap_values: Any,
    expected_value: Any,
) -> tuple[np.ndarray, float]:
    if isinstance(shap_values, (list, tuple)):
        if len(shap_values) == 2:
            shap_values = shap_values[1]
            if isinstance(expected_value, (list, tuple, np.ndarray)):
                expected_value = expected_value[1]
        elif len(shap_values) == 1:
            shap_values = shap_values[0]
        else:
            raise ValueError("M4: salida SHAP multiclase no soportada por esta validación")

    shap_array = np.asarray(shap_values)
    if shap_array.ndim == 1:
        shap_array = shap_array.reshape(1, -1)

    base_value = _select_positive_class_value(expected_value)
    return shap_array, base_value


def _predict_raw_margin(
    model: Any,
    features_frame: pd.DataFrame,
    iteration_range: tuple[int, int] | None,
) -> np.ndarray:
    predict_kwargs: dict[str, Any] = {"output_margin": True}
    if iteration_range is not None:
        predict_kwargs["iteration_range"] = iteration_range

    try:
        raw_predictions = model.predict(features_frame, **predict_kwargs)
    except TypeError:
        booster = model.get_booster() if hasattr(model, "get_booster") else model
        dmatrix = xgb.DMatrix(features_frame, feature_names=list(features_frame.columns))
        raw_predictions = booster.predict(dmatrix, **predict_kwargs)

    return np.asarray(raw_predictions).reshape(-1)


def _resolve_iteration_range(best_iteration: Any) -> tuple[int, int] | None:
    if best_iteration is None:
        return None
    return (0, int(best_iteration) + 1)


def _validate_math_for_cultivo(
    cultivo: str,
    df_features: pd.DataFrame,
    feature_cols: list[str],
    explainer: shap.TreeExplainer,
    model: Any,
    best_iteration: Any,
) -> None:
    df_cultivo = df_features[df_features["cultivo"] == cultivo].copy()
    assert not df_cultivo.empty, f"M4: no hay filas para el cultivo {cultivo} en feature_matrix.parquet"

    sample_size = min(10, len(df_cultivo))
    sampled_rows = df_cultivo.sample(n=sample_size, random_state=42)
    sampled_features = sampled_rows[feature_cols]

    shap_values = explainer.shap_values(sampled_features)
    shap_array, base_value = _normalize_shap_output(shap_values, explainer.expected_value)
    raw_margins = _predict_raw_margin(model, sampled_features, _resolve_iteration_range(best_iteration))

    assert shap_array.shape[0] == len(sampled_features), (
        f"M4: filas SHAP ({shap_array.shape[0]}) != filas muestreadas ({len(sampled_features)}) para {cultivo}"
    )
    assert shap_array.shape[1] == len(feature_cols), (
        f"M4: columnas SHAP ({shap_array.shape[1]}) != features ({len(feature_cols)}) para {cultivo}"
    )

    for row_position, (shap_row, raw_margin) in enumerate(zip(shap_array, raw_margins, strict=True)):
        shap_margin = float(np.sum(shap_row) + base_value)
        assert np.isclose(shap_margin, float(raw_margin), atol=1e-4), (
            f"M4: mismatch SHAP vs raw para {cultivo} fila {sampled_features.index[row_position]}: "
            f"shap={shap_margin:.6f} raw={float(raw_margin):.6f}"
        )


def _validate_narratives(df_output: pd.DataFrame) -> None:
    assert not df_output.empty, "M4: el parquet consolidado está vacío"
    assert OUTPUT_COLUMNS.issubset(df_output.columns), (
        f"M4: faltan columnas obligatorias en el parquet: {sorted(OUTPUT_COLUMNS - set(df_output.columns))}"
    )

    narrativa = df_output["narrativa_riesgo"]
    assert narrativa.notna().all(), "M4: hay valores nulos en narrativa_riesgo"

    narrative_lengths = narrativa.astype(str).str.len()
    assert float(narrative_lengths.mean()) > 15.0, (
        f"M4: la longitud promedio de narrativa_riesgo es demasiado baja ({float(narrative_lengths.mean()):.2f})"
    )

    sample_size = min(50, len(df_output))
    sampled_narratives = narrativa.dropna().sample(n=sample_size, random_state=42).astype(str)
    raw_feature_mask = sampled_narratives.str.contains(r"\b\w+_\w+\b", regex=True, na=False)
    if raw_feature_mask.any():
        offending_index = raw_feature_mask[raw_feature_mask].index[0]
        offending_text = sampled_narratives.loc[offending_index]
        raise AssertionError(
            f"M4: narrativa con feature cruda detectada en fila {offending_index}: {offending_text}"
        )

    # rendimiento_esperado: float64, no nulo
    assert pd.api.types.is_float_dtype(df_output["rendimiento_esperado"]), \
        "M4: rendimiento_esperado debe ser float64"
    assert df_output["rendimiento_esperado"].notna().all(), \
        "M4: rendimiento_esperado tiene valores nulos"

    # etiqueta_riesgo: string, valores válidos
    etiquetas_validas = {"Bajo", "Medio", "Alto"}
    assert set(df_output["etiqueta_riesgo"].dropna().unique()).issubset(etiquetas_validas), \
        "M4: etiqueta_riesgo contiene valores fuera de {'Bajo','Medio','Alto'}"
    assert df_output["etiqueta_riesgo"].notna().all(), \
        "M4: etiqueta_riesgo tiene valores nulos"


def validate_m4() -> None:
    """Ejecuta la validación del módulo M4."""
    print("Iniciando validacion de M4...")

    assert FEATURE_MATRIX_PATH.exists(), f"M4: falta feature_matrix.parquet en {FEATURE_MATRIX_PATH}"
    assert EXPLICACION_PATH.exists(), f"M4: falta predicciones_con_explicacion.parquet en {EXPLICACION_PATH}"

    df_features = pd.read_parquet(FEATURE_MATRIX_PATH)
    df_output = pd.read_parquet(EXPLICACION_PATH)

    for cultivo in CULTIVOS_MVP:
        explainer_path = EXPLAINER_PATHS[cultivo]
        model_path = _find_existing_path(MODEL_PATHS[cultivo])
        meta_path = META_PATHS[cultivo]

        assert explainer_path.exists(), f"M4: falta el explainer para {cultivo}: {explainer_path}"
        assert meta_path.exists(), f"M4: faltan los metadatos para {cultivo}: {meta_path}"

        meta = _load_json(meta_path)
        feature_cols = meta.get("feature_cols")
        assert isinstance(feature_cols, list) and feature_cols, (
            f"M4: feature_cols faltante o vacío en {meta_path}"
        )

        missing_columns = [column for column in feature_cols if column not in df_features.columns]
        assert not missing_columns, (
            f"M4: faltan columnas en feature_matrix para {cultivo}: {missing_columns}"
        )

        best_iteration = meta.get("best_iteration")
        assert best_iteration is not None, f"M4: best_iteration ausente para {cultivo}"
        assert int(best_iteration) >= 0, f"M4: best_iteration inválido para {cultivo}: {best_iteration}"

        explainer = _load_explainer(explainer_path)
        model = _load_model(model_path)

        _validate_math_for_cultivo(
            cultivo=cultivo,
            df_features=df_features,
            feature_cols=feature_cols,
            explainer=explainer,
            model=model,
            best_iteration=best_iteration,
        )

    _validate_narratives(df_output)

    print("[✔] M4: Los modelos TreeExplainer cargan correctamente.")
    print("[✔] M4: Suma total convergente con predicciones RAW (XGB).")
    print("[✔] M4: Textos libres e íntegros en variables (sin guiones bajos raw).")
    print("[✔] M4: 'predicciones_con_explicacion.parquet' persistido.")
    print("Validacion M4 aprobada exitosamente.")


def run_tests() -> None:
    """Compatibilidad con el nombre del script anterior."""
    validate_m4()


if __name__ == "__main__":
    validate_m4()
