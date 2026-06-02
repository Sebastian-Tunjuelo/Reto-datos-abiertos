import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def build_target_riesgo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye la etiqueta binaria target_riesgo por fila usando una caída de rendimiento
    mayor al 15% frente al promedio histórico calculado solo con años anteriores 
    del mismo codigo_dane y cultivo.
    """
    if df.empty:
        raise ValueError("[M3.1] tabla_maestra está vacía")
        
    required_cols = ['codigo_dane', 'cultivo', 'año', 'target_rendimiento']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Faltan columnas clave: {missing_cols}")
        
    duplicates = df[df.duplicated(subset=['codigo_dane', 'cultivo', 'año'], keep=False)]
    if not duplicates.empty:
        affected_groups = duplicates[['codigo_dane', 'cultivo', 'año']].head(1).to_dict('records')[0]
        raise ValueError(f"Llave duplicada encontrada (ejemplo): {affected_groups}")
        
    df_sorted = df.sort_values(by=['codigo_dane', 'cultivo', 'año']).copy()
    
    df_sorted['promedio_historico'] = (
        df_sorted.groupby(['codigo_dane', 'cultivo'])['target_rendimiento']
        .transform(lambda x: x.expanding(min_periods=1).mean().shift(1))
    )
    
    df_sorted['umbral_riesgo'] = df_sorted['promedio_historico'] * 0.85
    
    cond_risk = df_sorted['target_rendimiento'] < df_sorted['umbral_riesgo']
    df_sorted['target_riesgo'] = np.where(cond_risk, 1, 0)
    
    mask_invalido = df_sorted['promedio_historico'].isna() | df_sorted['target_rendimiento'].isna()
    
    filas_nulas = mask_invalido.sum()
    if filas_nulas > 0:
        logger.warning(f"[M3.1] {filas_nulas} filas sin historial suficiente o sin target_rendimiento "
                       f"(quedarán con target_riesgo=NaN y deben ser excluidas en M3.2).")

    df_sorted['target_riesgo'] = np.where(mask_invalido, np.nan, df_sorted['target_riesgo'])
    
    if df_sorted['target_riesgo'].isna().all():
        raise ValueError("Ninguna fila tiene target_riesgo calculable. El conjunto no sirve para entrenar M3.2")
        
    valid_mask = ~df_sorted['target_riesgo'].isna()
    if valid_mask.any():
        prop_positivos = df_sorted.loc[valid_mask, 'target_riesgo'].mean()
        positivos_count = int(df_sorted['target_riesgo'].sum())
        logger.info(f"[M3.1] Proporción de positivos (riesgo alto): {prop_positivos:.2%} ({positivos_count}/{valid_mask.sum()})")
        
    return df_sorted
