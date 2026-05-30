# FairBet Lab

Simulador **educativo** de apuestas deportivas con moneda virtual (S/ ficticios).
Proyecto del reto TLP — no es una casa de apuestas real.

## Inicio rápido

```bash
git clone <url-del-repo>
cd RetoTLP-2
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py seed_demo
```

Abre http://localhost:8000/

| URL | Descripción |
|-----|-------------|
| http://localhost:8000/ | Landing |
| http://localhost:8000/cuenta/ | Registro y login |
| http://localhost:8000/eventos/ | Partidos y cuotas |
| http://localhost:8000/api/health/ | Estado del API |

## Stack

- **Backend:** Django 5 + Django REST Framework
- **Base de datos:** PostgreSQL 16
- **Async:** Redis, Celery, Django Channels (WebSockets en puerto 8001)
- **Frontend:** Plantillas Django + CSS/JS vanilla (mobile-first)

## Estructura del repositorio

```
apps/
  users/    # KYC, perfil, juego responsable
  wallet/   # Libro mayor (partida doble)
  betting/  # Eventos, apuestas, cash-out, in-play
  audit/    # Cadena SHA256, operador, anti-fraude
config/     # settings, urls, celery, asgi
templates/  # Páginas HTML
static/     # CSS y JS (fairbet-*.js)
docs/       # Guías y ADRs
```

## Documentación

- [Instalación detallada](docs/guia-instalacion.md)
- [Mapa de páginas](docs/guia-paginas-frontend.md)
- [Entrega y video demo](docs/entrega-demo.md)
- [Índice de docs](docs/README.md)

## Video demo

Enlace a la grabación: _[añadir URL en docs/entrega-demo.md]_

## Tests

```bash
docker compose exec web pytest
```

## Juego responsable

Plataforma con fines **exclusivamente educativos**. Incluye límites de recarga,
autoexclusión y avisos legales. No uses dinero real ni la presentes como producto comercial.

## Equipo

| Integrante | Área |
|------------|------|
| 1 | Usuarios / KYC |
| 2 | Wallet |
| 3 | Apuestas |
| 4 | Auditoría / operador |
| 5 | Frontend general + entrega |

## Licencia

Proyecto académico — consultar con el docente del curso.
