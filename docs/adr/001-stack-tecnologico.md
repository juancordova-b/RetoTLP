# ADR-001 — Stack tecnológico

**Estado:** Aceptado  
**Fecha:** 2026-05-29

## Contexto

Necesitamos un simulador de apuestas deportivas con moneda virtual, contabilidad fiable,
cuotas en vivo y panel de operador. El equipo es pequeño y el plazo es acotado.

## Decisión

Usar:

- **Django 5 + DRF** — backend y API REST en un solo proyecto.
- **PostgreSQL 16** — datos relacionales (usuarios, apuestas, ledger).
- **Redis** — broker de Celery y capa de Channels (WebSockets).
- **Celery + django-celery-beat** — tareas diferidas (reactivar mercados).
- **Daphne (Channels)** — cuotas en vivo por WebSocket en puerto 8001.
- **Frontend** — plantillas Django + JavaScript vanilla (sin framework SPA).

## Motivos

| Opción | Ventaja para este proyecto |
|--------|---------------------------|
| Django | Admin incluido, ORM maduro, buen encaje con DRF |
| PostgreSQL | Transacciones ACID para partida doble del wallet |
| Redis | Ya lo exige Channels; reutilizamos para Celery |
| JS vanilla | Curva de aprendizaje baja; cada integrante toca su módulo |

## Consecuencias

- Positivo: un solo lenguaje principal (Python) en backend.
- Positivo: Docker Compose levanta todo el entorno con un comando.
- Negativo: el frontend no es SPA; la navegación recarga páginas completas.
- Negativo: WebSockets van en un proceso aparte (`channels` en compose).
