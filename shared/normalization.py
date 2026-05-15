"""
Utilidades de normalización de nombres de municipios y cultivos.
Necesario porque los datasets de datos.gov.co usan formatos distintos.
"""
import unicodedata


def normalize_name(name: str) -> str:
    """
    Normaliza un nombre de municipio para comparación entre datasets.
    Convierte a MAYÚSCULAS y elimina tildes/diacríticos.

    Ejemplos:
        'Ibagué'  → 'IBAGUE'
        'IBAGUÉ'  → 'IBAGUE'
        'ibague'  → 'IBAGUE'
        'San Vicente de Chucurí' → 'SAN VICENTE DE CHUCURI'
    """
    name = name.strip().upper()
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    return name


def normalize_cultivo(cultivo: str) -> str:
    """
    Normaliza el nombre de un cultivo al formato estándar del proyecto.
    Maneja tanto MAYÚSCULAS (EVA histórica) como Title Case (EVA reciente).

    Retorna: 'Café' | 'Cacao' | 'Maíz' | None si no reconocido
    """
    cultivo_norm = normalize_name(cultivo)
    mapping = {
        'CAFE': 'Café',
        'CAFÉ': 'Café',
        'CACAO': 'Cacao',
        'MAIZ': 'Maíz',
        'MAÍZ': 'Maíz',
    }
    return mapping.get(cultivo_norm)


def normalize_dane_code(code) -> str:
    """
    Normaliza un código DANE a string de 5 dígitos con cero a la izquierda.

    Ejemplos:
        5001  → '05001'
        '5001' → '05001'
        '05001' → '05001'
    """
    return str(int(str(code).strip())).zfill(5)


def normalize_title_case(name: str) -> str:
    """
    Convierte un nombre a Title Case preservando tildes.
    Útil para mostrar nombres en el frontend.

    Ejemplo: 'IBAGUÉ' → 'Ibagué'
    """
    return name.strip().title()
