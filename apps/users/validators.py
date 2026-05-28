"""
Validación de DNI peruano.

IMPORTANTE: El número de 8 dígitos del DNI (ej. 77814916) es el documento completo
emitido por RENIEC. El "dígito verificador" que aparece en algunas tarjetas físicas
se calcula con módulo 11 sobre los 8 dígitos y es un carácter aparte — NO siempre
coincide con el 8.º dígito del número.

El registro usa:
  1) DNI: exactamente 8 dígitos numéricos.
  2) Dígito verificador separado, calculado con módulo 11 sobre esos 8 dígitos.
"""
import re
from datetime import date

DNI_WEIGHTS = (3, 2, 7, 6, 5, 4, 3, 2)
SERIE_VERIFICADOR = "6789012345"  # índice según algoritmo módulo 11 (tarjeta DNI)


def validar_formato_dni(dni: str) -> bool:
    """True si tiene 8 dígitos numéricos (formato RENIEC estándar)."""
    dni = (dni or "").strip()
    if not re.fullmatch(r"\d{8}", dni):
        return False
    if dni == "00000000":
        return False
    return True


def calcular_digito_verificador_tarjeta(dni_ocho_digitos: str) -> str:
    """
    Dígito de la tarjeta DNI (RENIEC): módulo 11 con pesos 3,2,7,6,5,4,3,2,
    luego 11 - resto y conversión con la serie 6789012345 (sin revelar al usuario).
    """
    nums = [int(c) for c in dni_ocho_digitos[:8]]
    total = sum(n * w for n, w in zip(nums, DNI_WEIGHTS))
    resto = total % 11
    digito = 11 - resto
    if digito == 11:
        digito = 0
    elif digito == 10:
        digito = 0
    if digito == 0:
        return "0"
    return SERIE_VERIFICADOR[digito - 1]


def validar_dni_peruano(dni: str, digito_verificador: str) -> bool:
    """Valida DNI peruano de 8 dígitos + dígito verificador separado."""
    if not validar_formato_dni(dni):
        return False
    digito_verificador = (digito_verificador or "").strip().upper()
    if not re.fullmatch(r"\d", digito_verificador):
        return False
    return calcular_digito_verificador_tarjeta(dni) == digito_verificador


def es_mayor_de_edad(fecha_nacimiento: date, hoy: date | None = None) -> bool:
    """True si tiene 18 años o más a la fecha de referencia."""
    hoy = hoy or date.today()
    edad = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    return edad >= 18
