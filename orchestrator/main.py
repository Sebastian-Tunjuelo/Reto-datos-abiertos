from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List
import pandas as pd
import joblib
import json

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
