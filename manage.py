#!/usr/bin/env python
"""Punto de entrada de comandos Django (migrate, runserver, test, etc.)."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se encontró Django. ¿Está activo el contenedor o el venv?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
