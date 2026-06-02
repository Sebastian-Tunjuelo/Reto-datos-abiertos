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
MAX_RETRIES = int(os.getenv("SOCRATA_MAX_RETRIES", "5"))
RETRY_BACKOFF = [5, 10, 30, 60, 90]  # segundos (escalado para consultas agregadas)
REQUEST_TIMEOUT = int(os.getenv("SOCRATA_TIMEOUT", "900"))  # 15 min para $group queries


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
            # Timeout más largo si hay $group (consultas agregadas)
            timeout = REQUEST_TIMEOUT if not group else REQUEST_TIMEOUT * 1.5
            resp = requests.get(
                url,
                params=params,
                headers=_get_headers(),
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.debug(
                "fetch %s offset=%d → %d registros", dataset_id, offset, len(data)
            )
            return data
        except requests.RequestException as e:
            logger.warning(
                "Intento %d/%d fallido para %s (espera %ds): %s", attempt, MAX_RETRIES, dataset_id, wait, e
            )
            if attempt < MAX_RETRIES:
                logger.info("Esperando %d segundos antes de reintentar…", wait)
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


def get_view_metadata(dataset_id: str) -> dict:
    """Obtiene la metadata de la vista Socrata (/api/views/{id})."""
    url = f"https://www.datos.gov.co/api/views/{dataset_id}.json"
    resp = requests.get(url, headers=_get_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_csv_export_url(dataset_id: str) -> str | None:
    """Intenta extraer la URL de export CSV desde la metadata de la vista.

    Retorna la URL absoluta si se encuentra, o None si no existe.
    """
    try:
        meta = get_view_metadata(dataset_id)
    except Exception:
        return None

    # Buscar en varias rutas posibles
    candidates = []
    md = meta.get("metadata", {})
    access = md.get("accessPoints") or md.get("additionalAccessPoints") or {}
    if isinstance(access, dict):
        # accessPoints puede mapear mime -> url
        candidates.extend(access.values())
    elif isinstance(access, list):
        for a in access:
            if isinstance(a, dict):
                candidates.append(a.get("url") or a.get("accessPoint"))

    # También revisar exports en top-level
    exports = md.get("exports") or meta.get("export") or {}
    if isinstance(exports, dict):
        candidates.extend(exports.values())

    # Filtrar urls que contengan .csv
    for c in candidates:
        if not c:
            continue
        if isinstance(c, str) and ".csv" in c:
            return c

    return None


def download_csv_export(dataset_id: str, dest_path: str) -> str:
    """Descarga el CSV de exportación del dataset si existe. Retorna la ruta de archivo.

    Lanza `requests.RequestException` si falla la descarga.
    """
    url = get_csv_export_url(dataset_id)
    if not url:
        raise ValueError(f"No se encontró export CSV para dataset {dataset_id}")

    resp = requests.get(url, headers=_get_headers(), stream=True, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    with open(dest_path, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                fh.write(chunk)
    return dest_path
