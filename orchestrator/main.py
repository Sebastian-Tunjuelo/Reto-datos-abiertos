from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import joblib
import json

from modules.agricultural.ingestion import load_eva_completa
from modules.climate.ingestion import load_clima_agregado
from modules.predictive.feature_builder import _agregar_anual, _pendiente_3a
from modules.predictive.scenarios import simulate_scenarios, SCENARIO_CATALOG

from shared.dane_codes import MVP_CODIGOS, DANE_TO_NAME, DANE_TO_DEPT, get_codigo
from shared.normalization import normalize_dane_code, normalize_cultivo, normalize_name
from shared.config import CULTIVOS_MVP, UMBRAL_RIESGO_MEDIO, UMBRAL_RIESGO_ALTO, DATA_DIR, MODELS_DIR

app = FastAPI(title="SiembraSegura IA API", version="1.0.0")

class MunicipioItem(BaseModel):
    codigo_dane: str
    municipio: str
    departamento: str

class CultivosMunicipioResponse(BaseModel):
    codigo_dane: str
    municipio: str
    departamento: str
    cultivos: List[str]

class PrediccionRequest(BaseModel):
    municipio: str
    cultivo: str
    año: int

class PrediccionResponse(BaseModel):
    codigo_dane: str
    municipio: str
    departamento: str
    cultivo: str
    año: int
    rendimiento_esperado: float
    prob_riesgo_alto: float
    etiqueta_riesgo: str

class EscenarioRequest(BaseModel):
    municipio: str
    cultivo: str
    año: int
    escenarios: Optional[List[str]] = None

class EscenarioResultado(BaseModel):
    escenario: str
    rendimiento_esperado: float
    prob_riesgo_alto: float
    etiqueta_riesgo: str
    delta_rendimiento_abs: float
    delta_rendimiento_pct: float
    delta_prob_riesgo_alto: float
    features_modificadas: List[str]
    supuesto: str

class EscenarioResponse(BaseModel):
    codigo_dane: str
    municipio: str
    departamento: str
    cultivo: str
    año: int
    escenarios_solicitados: List[str]
    resultados: List[EscenarioResultado]

class RendimientoHistoricoData(BaseModel):
    año: int
    rendimiento: Optional[float]
    area_sembrada: Optional[float]
    rendimiento_prom3a: Optional[float]
    tendencia_3a: Optional[float]

class RendimientoHistoricoResponse(BaseModel):
    codigo_dane: str
    municipio: str
    departamento: str
    cultivo: str
    n_anios: int
    año_min: int
    año_max: int
    serie: List[RendimientoHistoricoData]

class SerieClimaticaData(BaseModel):
    año: int
    prec_acum_mm: Optional[float]
    prec_dias_secos: Optional[int]
    prec_dias_lluvia: Optional[int]
    temp_media_c: Optional[float]
    temp_max_media_c: Optional[float]
    hum_media_pct: Optional[float]
    n_estaciones_prec: int
    n_estaciones_temp: int
    anomalia_prec: Optional[float]
    anomalia_temp: Optional[float]

class SerieClimaticaResponse(BaseModel):
    codigo_dane: str
    municipio: str
    departamento: str
    n_anios: int
    año_min: int
    año_max: int
    serie: List[SerieClimaticaData]

@app.get("/municipios", response_model=List[MunicipioItem])
def get_municipios():
    items = []
    seen = set()
    for codigo in MVP_CODIGOS:
        codigo_norm = normalize_dane_code(codigo)
        if codigo_norm in seen:
            raise HTTPException(status_code=500, detail="Catálogo de municipios inconsistente")
        if codigo_norm not in DANE_TO_NAME or codigo_norm not in DANE_TO_DEPT:
            raise HTTPException(status_code=500, detail="Catálogo de municipios inconsistente")
        
        items.append(MunicipioItem(
            codigo_dane=codigo_norm,
            municipio=DANE_TO_NAME[codigo_norm],
            departamento=DANE_TO_DEPT[codigo_norm]
        ))
        seen.add(codigo_norm)
    if len(items) != 15:
        raise HTTPException(status_code=500, detail="Catálogo de municipios inconsistente")
    return items

@app.get("/cultivos/{municipio}", response_model=CultivosMunicipioResponse)
def get_cultivos_por_municipio(municipio: str):
    if municipio.isdigit():
        codigo_norm = normalize_dane_code(municipio)
    else:
        codigo_norm = get_codigo(municipio)
    
    if not codigo_norm or codigo_norm not in MVP_CODIGOS:
        raise HTTPException(status_code=404, detail="Municipio no encontrado en el MVP")

    parquet_path = DATA_DIR / "feature_matrix.parquet"
    if not parquet_path.exists():
        raise HTTPException(status_code=503, detail="feature_matrix.parquet no disponible")
    
    try:
        df = pd.read_parquet(parquet_path, columns=["codigo_dane", "municipio", "departamento", "cultivo"])
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno al resolver cultivos por municipio")
    
    df["codigo_dane"] = df["codigo_dane"].astype(str).str.zfill(5)
    df_filtered = df[df["codigo_dane"] == codigo_norm]
    
    if df_filtered.empty:
        raise HTTPException(status_code=404, detail="No hay cultivos disponibles para el municipio solicitado")
    
    cultivos_presentes = df_filtered["cultivo"].dropna().unique().tolist()
    cultivos_presentes_norm = []
    for c in cultivos_presentes:
        c_norm = normalize_cultivo(c)
        if c_norm and c_norm in CULTIVOS_MVP:
            cultivos_presentes_norm.append(c_norm)
    
    cultivos_presentes_norm = list(set(cultivos_presentes_norm))
    if not cultivos_presentes_norm:
        raise HTTPException(status_code=404, detail="No hay cultivos disponibles para el municipio solicitado")
        
    cultivos_ordenados = [c for c in CULTIVOS_MVP if c in cultivos_presentes_norm]
    
    return CultivosMunicipioResponse(
        codigo_dane=codigo_norm,
        municipio=DANE_TO_NAME[codigo_norm],
        departamento=DANE_TO_DEPT[codigo_norm],
        cultivos=cultivos_ordenados
    )

@app.get("/rendimiento/{municipio}/{cultivo}", response_model=RendimientoHistoricoResponse)
def get_rendimiento_historico(municipio: str, cultivo: str):
    if str(municipio).isdigit():
        codigo_norm = normalize_dane_code(municipio)
    else:
        codigo_norm = get_codigo(municipio)
        
    if not codigo_norm or codigo_norm not in MVP_CODIGOS:
        raise HTTPException(status_code=404, detail="Municipio no encontrado en el MVP")

    cultivo_norm = normalize_cultivo(cultivo)
    if not cultivo_norm or cultivo_norm not in CULTIVOS_MVP:
        raise HTTPException(status_code=422, detail="Cultivo inválido. Valores permitidos: Café, Cacao, Maíz")

    try:
        df_eva = load_eva_completa()
    except Exception:
        raise HTTPException(status_code=503, detail="eva_completa.parquet no disponible")
        
    req_cols = {"codigo_dane", "municipio", "departamento", "cultivo", "año", "rendimiento", "area_sembrada"}
    if not req_cols.issubset(df_eva.columns):
        raise HTTPException(status_code=503, detail="eva_completa.parquet no disponible")
    
    # Cast año to int safely if needed, ensure it strings match properly if needed
    df_eva["año"] = pd.to_numeric(df_eva["año"], errors="coerce")
    df_eva = df_eva.dropna(subset=["año"])
    df_eva["año"] = df_eva["año"].astype(int)

    df_filtered = df_eva[(df_eva["codigo_dane"].astype(str).str.zfill(5) == codigo_norm) & (df_eva["cultivo"] == cultivo_norm)]
    if df_filtered.empty:
        raise HTTPException(status_code=404, detail="No hay datos históricos suficientes para la combinación solicitada")
    
    try:
        df_agg = _agregar_anual(df_filtered)
        df_agg = df_agg.sort_values(by="año", ascending=True).reset_index(drop=True)
        
        rendimiento_prom3a = df_agg["rendimiento"].shift(1).rolling(window=3, min_periods=1).mean()
        tendencia_3a = _pendiente_3a(df_agg["rendimiento"])
        
        df_agg["rendimiento_prom3a"] = rendimiento_prom3a
        df_agg["tendencia_3a"] = tendencia_3a
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno al resolver la serie histórica de rendimiento")

    if df_agg.empty:
        raise HTTPException(status_code=404, detail="No hay datos históricos suficientes para la combinación solicitada")

    serie = []
    for _, row in df_agg.iterrows():
        serie.append(RendimientoHistoricoData(
            año=int(row["año"]),
            rendimiento=round(float(row["rendimiento"]), 2) if pd.notna(row["rendimiento"]) else None,
            area_sembrada=round(float(row["area_sembrada"]), 2) if pd.notna(row["area_sembrada"]) else None,
            rendimiento_prom3a=round(float(row["rendimiento_prom3a"]), 2) if pd.notna(row["rendimiento_prom3a"]) else None,
            tendencia_3a=round(float(row["tendencia_3a"]), 2) if pd.notna(row["tendencia_3a"]) else None
        ))
        
    return RendimientoHistoricoResponse(
        codigo_dane=codigo_norm,
        municipio=DANE_TO_NAME[codigo_norm],
        departamento=DANE_TO_DEPT[codigo_norm],
        cultivo=cultivo_norm,
        n_anios=len(serie),
        año_min=serie[0].año,
        año_max=serie[-1].año,
        serie=serie
    )

@app.get("/clima/{municipio}", response_model=SerieClimaticaResponse)
def get_clima_historico(municipio: str):
    if str(municipio).isdigit():
        codigo_norm = normalize_dane_code(municipio)
    else:
        codigo_norm = get_codigo(municipio)
        
    if not codigo_norm or codigo_norm not in MVP_CODIGOS:
        raise HTTPException(status_code=404, detail="Municipio no encontrado en el MVP")

    try:
        df_clima = load_clima_agregado()
    except Exception:
        raise HTTPException(status_code=503, detail="clima_agregado.parquet no disponible")
        
    req_cols = {"codigo_dane", "año", "prec_acum_mm", "temp_media_c"}
    if not req_cols.issubset(df_clima.columns) and not {"dias_secos"}.issubset(df_clima.columns) and not {"prec_dias_secos"}.issubset(df_clima.columns):
        if not {"codigo_dane", "año", "prec_acum_mm"}.issubset(df_clima.columns):
            raise HTTPException(status_code=503, detail="clima_agregado.parquet no disponible")
    
    if "dias_secos" in df_clima.columns and "prec_dias_secos" not in df_clima.columns:
        df_clima = df_clima.rename(columns={"dias_secos": "prec_dias_secos"})

    df_clima["año"] = pd.to_numeric(df_clima["año"], errors="coerce")
    df_clima = df_clima.dropna(subset=["año"])
    
    df_filtered = df_clima[df_clima["codigo_dane"].astype(str).str.zfill(5) == codigo_norm]
    if df_filtered.empty:
        raise HTTPException(status_code=404, detail="No hay datos climáticos disponibles para el municipio solicitado")
    
    try:
        df_filtered = df_filtered.sort_values(by="año", ascending=True).reset_index(drop=True)
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno al resolver la serie climática")

    if df_filtered.empty:
        raise HTTPException(status_code=404, detail="No hay datos climáticos disponibles para el municipio solicitado")

    serie = []
    for _, row in df_filtered.iterrows():
        serie.append(SerieClimaticaData(
            año=int(row["año"]),
            prec_acum_mm=round(float(row["prec_acum_mm"]), 2) if "prec_acum_mm" in row and pd.notna(row.get("prec_acum_mm")) else None,
            prec_dias_secos=int(row["prec_dias_secos"]) if "prec_dias_secos" in row and pd.notna(row.get("prec_dias_secos")) else None,
            prec_dias_lluvia=int(row["prec_dias_lluvia"]) if "prec_dias_lluvia" in row and pd.notna(row.get("prec_dias_lluvia")) else None,
            temp_media_c=round(float(row["temp_media_c"]), 2) if "temp_media_c" in row and pd.notna(row.get("temp_media_c")) else None,
            temp_max_media_c=round(float(row["temp_max_media_c"]), 2) if "temp_max_media_c" in row and pd.notna(row.get("temp_max_media_c")) else None,
            hum_media_pct=round(float(row["hum_media_pct"]), 2) if "hum_media_pct" in row and pd.notna(row.get("hum_media_pct")) else None,
            n_estaciones_prec=int(row["n_estaciones_prec"]) if "n_estaciones_prec" in row and pd.notna(row.get("n_estaciones_prec")) else 0,
            n_estaciones_temp=int(row["n_estaciones_temp"]) if "n_estaciones_temp" in row and pd.notna(row.get("n_estaciones_temp")) else 0,
            anomalia_prec=round(float(row["anomalia_prec"]), 3) if "anomalia_prec" in row and pd.notna(row.get("anomalia_prec")) else None,
            anomalia_temp=round(float(row["anomalia_temp"]), 3) if "anomalia_temp" in row and pd.notna(row.get("anomalia_temp")) else None
        ))
        
    return SerieClimaticaResponse(
        codigo_dane=codigo_norm,
        municipio=DANE_TO_NAME[codigo_norm],
        departamento=DANE_TO_DEPT[codigo_norm],
        n_anios=len(serie),
        año_min=serie[0].año,
        año_max=serie[-1].año,
        serie=serie
    )


@app.post("/predecir", response_model=PrediccionResponse)
def predecir(req: PrediccionRequest):
    if str(req.municipio).isdigit():
        codigo_norm = normalize_dane_code(req.municipio)
    else:
        codigo_norm = get_codigo(req.municipio)
        
    if not codigo_norm or codigo_norm not in MVP_CODIGOS:
        raise HTTPException(status_code=404, detail="Municipio no encontrado en el MVP")
        
    cultivo_norm = normalize_cultivo(req.cultivo)
    if not cultivo_norm or cultivo_norm not in CULTIVOS_MVP:
        raise HTTPException(status_code=422, detail="Cultivo inválido o no soportado")
        
    parquet_path = DATA_DIR / "feature_matrix.parquet"
    if not parquet_path.exists():
        raise HTTPException(status_code=503, detail="feature_matrix.parquet no disponible")
    
    df = pd.read_parquet(parquet_path)
    df["codigo_dane"] = df["codigo_dane"].astype(str).str.zfill(5)
    
    def __norm_cult(c): return normalize_cultivo(c)
    df["cultivo_norm"] = df["cultivo"].apply(__norm_cult)
    
    df_filtered = df[(df["codigo_dane"] == codigo_norm) & (df["cultivo_norm"] == cultivo_norm)].copy()
    if df_filtered.empty:
        raise HTTPException(status_code=404, detail="No hay datos históricos para este municipio y cultivo")
    
    max_year = df_filtered["año"].max()
    if req.año <= max_year:
        raise HTTPException(status_code=422, detail="El año objetivo debe ser futuro (mayor al último dato histórico)")
    
    last_row = df_filtered[df_filtered["año"] == max_year].iloc[0]
    
    c_file = normalize_name(cultivo_norm).lower()
    
    reg_model_path = MODELS_DIR / f"xgb_regressor_{c_file}.pkl"
    reg_meta_path = MODELS_DIR / f"xgb_regressor_{c_file}_meta.json"
    clf_model_path = MODELS_DIR / f"xgb_classifier_{c_file}.pkl"
    clf_meta_path = MODELS_DIR / f"xgb_classifier_{c_file}_meta.json"
    
    if not (reg_model_path.exists() and reg_meta_path.exists() and clf_model_path.exists() and clf_meta_path.exists()):
        raise HTTPException(status_code=500, detail="Modelos o metadatos no encontrados para el cultivo solicitado")
    
    with open(reg_meta_path, "r", encoding="utf-8") as f:
        reg_meta = json.load(f)
    with open(clf_meta_path, "r", encoding="utf-8") as f:
        clf_meta = json.load(f)
        
    reg_features = reg_meta.get("features", [])
    clf_features = clf_meta.get("features", [])
    
    row_dict = last_row.to_dict()
    row_dict["año"] = req.año
    
    def build_vector(feats):
        return [row_dict.get(feat, 0) for feat in feats]

    X_reg = pd.DataFrame([build_vector(reg_features)], columns=reg_features)
    X_clf = pd.DataFrame([build_vector(clf_features)], columns=clf_features)
    
    regressor = joblib.load(reg_model_path)
    rend_esperado = float(regressor.predict(X_reg)[0])
    
    classifier = joblib.load(clf_model_path)
    probas = classifier.predict_proba(X_clf)[0]
    
    classes_ = getattr(classifier, "classes_", [0, 1, 2])
    if len(probas) == 2:
        prob_alto = float(probas[1])
    elif len(probas) > 2:
        if 2 in classes_:
            idx = list(classes_).index(2)
            prob_alto = float(probas[idx])
        else:
            prob_alto = float(probas[-1])
    else:
        prob_alto = 0.0
        
    if prob_alto >= UMBRAL_RIESGO_ALTO:
        etiqueta = "Alto"
    elif prob_alto >= UMBRAL_RIESGO_MEDIO:
        etiqueta = "Medio"
    else:
        etiqueta = "Bajo"
        
    return PrediccionResponse(
        codigo_dane=codigo_norm,
        municipio=DANE_TO_NAME[codigo_norm],
        departamento=DANE_TO_DEPT[codigo_norm],
        cultivo=cultivo_norm,
        año=req.año,
        rendimiento_esperado=round(rend_esperado, 2),
        prob_riesgo_alto=round(prob_alto, 3),
        etiqueta_riesgo=etiqueta
    )

@app.post('/escenario', response_model=EscenarioResponse)
def post_escenario(req: EscenarioRequest):
    if str(req.municipio).isdigit():
        codigo_norm = normalize_dane_code(req.municipio)
    else:
        codigo_norm = get_codigo(req.municipio)
        
    if not codigo_norm or codigo_norm not in MVP_CODIGOS:
        raise HTTPException(status_code=404, detail='Municipio no encontrado en el MVP')

    cultivo_norm = normalize_cultivo(req.cultivo)
    if not cultivo_norm or cultivo_norm not in CULTIVOS_MVP:
        raise HTTPException(status_code=422, detail='Cultivo inválido. Valores permitidos: Café, Cacao, Maíz')

    if not isinstance(req.año, int):
        raise HTTPException(status_code=422, detail='Año objetivo inválido para simulación')

    escenarios_req = req.escenarios if req.escenarios is not None else SCENARIO_CATALOG
    
    esc_limpios = []
    esc_limpios.append('base')
        
    for e in escenarios_req:
        if e not in SCENARIO_CATALOG:
            raise HTTPException(status_code=422, detail='Escenario inválido. Valores permitidos: base, seco, lluvioso, fertilizantes')
        if e != 'base' and e not in esc_limpios:
            esc_limpios.append(e)

    parquet_path = DATA_DIR / 'feature_matrix.parquet'
    if not parquet_path.exists():
        raise HTTPException(status_code=503, detail='feature_matrix.parquet no disponible')
    
    try:
        df = pd.read_parquet(parquet_path)
    except Exception:
        raise HTTPException(status_code=503, detail='feature_matrix.parquet no disponible')
        
    df['codigo_dane'] = df['codigo_dane'].astype(str).str.zfill(5)
    df_filtered = df[(df['codigo_dane'] == codigo_norm) & (df['cultivo'] == cultivo_norm)].copy()
    
    if df_filtered.empty:
        raise HTTPException(status_code=404, detail='No hay datos históricos suficientes para la combinación solicitada')
        
    df_filtered['año'] = pd.to_numeric(df_filtered['año'], errors='coerce')
    max_año_historico = int(df_filtered['año'].max())
    
    if req.año <= max_año_historico:
        raise HTTPException(status_code=422, detail='Año objetivo inválido para simulación')
        
    baseline_row = df_filtered[df_filtered['año'] == max_año_historico].copy()
    baseline_row['año'] = req.año
    
    try:
        df_resultados = simulate_scenarios(baseline_row, esc_limpios)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail='Artefactos de escenarios no disponibles')
    except KeyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail='Error interno en la API de escenarios')
        
    resultados = []
    for _, r in df_resultados.iterrows():
        resultados.append(EscenarioResultado(
            escenario=r['escenario'],
            rendimiento_esperado=r['rendimiento_esperado'],
            prob_riesgo_alto=r['prob_riesgo_alto'],
            etiqueta_riesgo=r['etiqueta_riesgo'],
            delta_rendimiento_abs=r['delta_rendimiento_abs'],
            delta_rendimiento_pct=r['delta_rendimiento_pct'],
            delta_prob_riesgo_alto=r['delta_prob_riesgo_alto'],
            features_modificadas=r['features_modificadas'],
            supuesto=r['supuesto']
        ))
        
    return EscenarioResponse(
        codigo_dane=codigo_norm,
        municipio=DANE_TO_NAME[codigo_norm],
        departamento=DANE_TO_DEPT[codigo_norm],
        cultivo=cultivo_norm,
        año=req.año,
        escenarios_solicitados=esc_limpios,
        resultados=resultados
    )
