"""
Herramienta interna para la demo: calcula el dígito verificador de un DNI.
No se expone en la API pública (el registro nunca debe revelar la respuesta).

Uso:
  docker compose exec web python manage.py digito_dni 77814916
"""
from django.core.management.base import BaseCommand

from apps.users.validators import calcular_digito_verificador_tarjeta, validar_formato_dni


class Command(BaseCommand):
    help = "Calcula el dígito verificador de un DNI (solo uso del equipo en demo)."

    def add_arguments(self, parser):
        parser.add_argument("dni", type=str, help="DNI de 8 dígitos")

    def handle(self, *args, **options):
        dni = options["dni"].strip()
        if not validar_formato_dni(dni):
            self.stderr.write(self.style.ERROR("DNI inválido: deben ser 8 dígitos numéricos."))
            return
        digito = calcular_digito_verificador_tarjeta(dni)
        self.stdout.write(
            self.style.SUCCESS(f"DNI {dni} → dígito verificador según módulo 11: {digito}")
        )
