"""
Cliente HTTP para la API Socrata de datos.gov.co.
Maneja paginación, reintentos y autenticación opcional.
"""
import logging
import time
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.datos.gov.co/resource"
DEFAULT_LIMIT = 5000
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]  # segundos


def _get_headers() -> dict:
    token = os.getenv("SOCRATA_APP_TOKEN", "")
    if token:
        return {"X-App-Token": token}
    return {}


def fetch(
    dataset_id: str,
    select: str | None = None,
    where: str | None = None,
    group: str | None = None,
    order: str | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> list[dict]:
    """
    Hace una sola llamada a la API Socrata con los parámetros dados.
    Reintenta hasta MAX_RETRIES veces ante errores de red.

    Returns:
        Lista de registros como dicts.
    """
    url = f"{BASE_URL}/{dataset_id}.json"
    params: dict[str, Any] = {"$limit": limit, "$offset": offset}
    if select:
        params["$select"] = select
    if where:
        params["$where"] = where
    if group:
        params["$group"] = group
    if order:
        params["$order"] = order

    for attempt, wait in enumerate(RETRY_BACKOFF, 1):
        try:
            resp = requests.get(url, params=params, headers=_get_headers(), timeout=30)
            resp.raise_for_status()
            data = resp.json()
            logger.debug(
                "fetch %s offset=%d → %d registros", dataset_id, offset, len(data)
            )
            return data
        except requests.RequestException as e:
            logger.warning(
                "Intento %d/%d fallido para %s: %s", attempt, MAX_RETRIES, dataset_id, e
            )
            if attempt < MAX_RETRIES:
                time.sleep(wait)
            else:
                raise


def fetch_all(
    dataset_id: str,
    select: str | None = None,
    where: str | None = None,
    group: str | None = None,
    order: str | None = None,
    page_size: int = DEFAULT_LIMIT,
) -> list[dict]:
    """
    Descarga TODOS los registros de un dataset paginando automáticamente.
    Útil cuando no se sabe cuántos registros hay.

    Returns:
        Lista completa de registros.
    """
    all_records: list[dict] = []
    offset = 0

    while True:
        batch = fetch(
            dataset_id,
            select=select,
            where=where,
            group=group,
            order=order,
            limit=page_size,
            offset=offset,
        )
        all_records.extend(batch)
        logger.info(
            "Dataset %s: descargados %d registros (offset=%d)",
            dataset_id, len(all_records), offset,
        )
        if len(batch) < page_size:
            break
        offset += page_size

    return all_records
