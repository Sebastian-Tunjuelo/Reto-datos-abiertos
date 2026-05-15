"""
Mapa de municipios del MVP a códigos DANE.
Llave de unión entre todos los datasets.
"""

# Municipios del MVP: nombre normalizado → código DANE (5 dígitos, string)
DANE_CODES: dict[str, str] = {
    "IBAGUE": "73001",
    "CHAPARRAL": "73168",
    "NEIVA": "41001",
    "GARZON": "41298",
    "PITALITO": "41551",
    "SAN VICENTE DE CHUCURI": "68689",
    "RIONEGRO": "68615",
    "ANORI": "05036",
    "AMALFI": "05030",
    "PENSILVANIA": "17541",
    "PALESTINA": "17524",
    "VILLAVICENCIO": "50001",
    "EL TAMBO": "19256",
    "MIRANDA": "19418",
    "VALLEDUPAR": "20001",
}

# Inverso: código DANE → nombre display (Title Case)
DANE_TO_NAME: dict[str, str] = {
    "73001": "Ibagué",
    "73168": "Chaparral",
    "41001": "Neiva",
    "41298": "Garzón",
    "41551": "Pitalito",
    "68689": "San Vicente de Chucurí",
    "68615": "Rionegro",
    "05036": "Anorí",
    "05030": "Amalfi",
    "17541": "Pensilvania",
    "17524": "Palestina",
    "50001": "Villavicencio",
    "19256": "El Tambo",
    "19418": "Miranda",
    "20001": "Valledupar",
}

# Departamentos de los municipios del MVP
DANE_TO_DEPT: dict[str, str] = {
    "73001": "Tolima",
    "73168": "Tolima",
    "41001": "Huila",
    "41298": "Huila",
    "41551": "Huila",
    "68689": "Santander",
    "68615": "Santander",
    "05036": "Antioquia",
    "05030": "Antioquia",
    "17541": "Caldas",
    "17524": "Caldas",
    "50001": "Meta",
    "19256": "Cauca",
    "19418": "Cauca",
    "20001": "Cesar",
}

MVP_MUNICIPIOS = list(DANE_TO_NAME.values())
MVP_CODIGOS = list(DANE_TO_NAME.keys())


def get_codigo(municipio_nombre: str) -> str | None:
    """Retorna el código DANE dado un nombre de municipio (cualquier formato)."""
    from shared.normalization import normalize_name
    key = normalize_name(municipio_nombre)
    return DANE_CODES.get(key)


def get_nombre(codigo_dane: str) -> str | None:
    """Retorna el nombre display dado un código DANE."""
    codigo = str(codigo_dane).zfill(5)
    return DANE_TO_NAME.get(codigo)
