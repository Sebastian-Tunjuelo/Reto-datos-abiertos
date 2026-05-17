"""
D2.4 — Cálculo de anomalías climáticas.

Función:
    calcular_anomalias()  ← D2.4
"""
import logging

import pandas as pd

from shared.config import TRAIN_HASTA
from shared.dane_codes import DANE_TO_NAME, MVP_CODIGOS

logger = logging.getLogger(__name__)


def calcular_anomalias(
    df: pd.DataFrame,
    año_corte: int = TRAIN_HASTA,
) -> pd.DataFrame:
    """
    Añade columnas anomalia_prec y anomalia_temp al DataFrame climático.

    La anomalía de precipitación es fraccional: (valor - media_hist) / media_hist.
    La anomalía de temperatura es absoluta: valor - media_hist (°C).
    El período de referencia es año <= año_corte.

    Args:
        df: DataFrame con columnas codigo_dane, año, prec_acum_mm, temp_media_c.
        año_corte: Último año del período histórico de referencia.
                   Default: TRAIN_HASTA (2021).

    Returns:
        df con columnas anomalia_prec y anomalia_temp añadidas.
        Los valores originales no se modifican.
    """
    df = df.copy()

    # Inicializar columnas de anomalía con NaN
    df["anomalia_prec"] = float("nan")
    df["anomalia_temp"] = float("nan")

    codigos = df["codigo_dane"].dropna().unique()

    for codigo in codigos:
        nombre = DANE_TO_NAME.get(codigo, codigo)
        mask_municipio = df["codigo_dane"] == codigo
        mask_hist = mask_municipio & (df["año"] <= año_corte)

        # ── Anomalía de precipitación ─────────────────────────────────────────
        prec_hist = df.loc[mask_hist, "prec_acum_mm"].dropna()
        n_prec = len(prec_hist)

        if n_prec < 3:
            logger.warning(
                "[D2.4] %s (%s): solo %d años de datos históricos para prec_acum_mm "
                "— anomalía poco confiable",
                nombre, codigo, n_prec,
            )

        if n_prec == 0:
            media_hist_prec = float("nan")
        else:
            media_hist_prec = float(prec_hist.mean())

        logger.info(
            "[D2.4] %s (%s): media histórica precipitación = %.1f mm (%d años)",
            nombre, codigo, media_hist_prec if not pd.isna(media_hist_prec) else -1,
            n_prec,
        )

        if pd.isna(media_hist_prec) or media_hist_prec == 0:
            if media_hist_prec == 0:
                logger.warning(
                    "[D2.4] %s (%s): media histórica de precipitación = 0 "
                    "— anomalia_prec = None",
                    nombre, codigo,
                )
            # anomalia_prec permanece NaN
        else:
            df.loc[mask_municipio, "anomalia_prec"] = (
                (df.loc[mask_municipio, "prec_acum_mm"] - media_hist_prec) / media_hist_prec
            )

        # ── Anomalía de temperatura ───────────────────────────────────────────
        temp_hist = df.loc[mask_hist, "temp_media_c"].dropna()
        n_temp = len(temp_hist)

        if n_temp < 3:
            logger.warning(
                "[D2.4] %s (%s): solo %d años de datos históricos para temp_media_c "
                "— anomalía poco confiable",
                nombre, codigo, n_temp,
            )

        if n_temp == 0:
            media_hist_temp = float("nan")
        else:
            media_hist_temp = float(temp_hist.mean())

        logger.info(
            "[D2.4] %s (%s): media histórica temperatura = %.2f °C (%d años)",
            nombre, codigo, media_hist_temp if not pd.isna(media_hist_temp) else -1,
            n_temp,
        )

        if pd.isna(media_hist_temp):
            # anomalia_temp permanece NaN
            pass
        else:
            df.loc[mask_municipio, "anomalia_temp"] = (
                df.loc[mask_municipio, "temp_media_c"] - media_hist_temp
            )

    return df
