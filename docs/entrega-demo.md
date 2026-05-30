# Guía de entrega — Integrante 5

Checklist para la presentación final del simulador FairBet Lab.

## Video demo

> Sustituye el enlace de abajo por tu grabación (YouTube, Drive, Loom, etc.)

**Enlace al video:** _[PENDIENTE — pegar URL aquí]_

### Guión sugerido (5–8 minutos)

1. **Intro (30 s)** — Qué es FairBet Lab y aviso de moneda virtual.
2. **Arranque (1 min)** — `docker compose up`, health check en `/api/health/`.
3. **Registro (1 min)** — Crear cuenta, KYC simulado, límites de juego responsable.
4. **Cartera (1 min)** — Recarga de S/ ficticios y consulta de saldo.
5. **Apuestas (2 min)** — Eventos, apuesta simple, opcional combinada o cash-out.
6. **Operador (1 min)** — Dashboard staff, verificación de auditoría SHA256.
7. **Cierre (30 s)** — Stack, equipo y referencia educativa MINCETUR.

## Checklist de entrega

- [ ] Repositorio accesible para el docente
- [ ] `README.md` con instrucciones de arranque
- [ ] `docker compose up -d --build` funciona en máquina limpia
- [ ] `seed_demo` ejecutado (eventos visibles en `/eventos/`)
- [ ] Video demo subido o enlace en este archivo y en README
- [ ] Páginas web probadas en móvil (DevTools ≤ 640 px)
- [ ] Usuario staff creado para panel `/operador/`

## Archivos del Integrante 5

| Archivo | Rol |
|---------|-----|
| `templates/base.html` | Layout común, nav, saldo, footer |
| `templates/home.html` | Landing |
| `static/css/fairbet.css` | Estilos mobile-first globales |
| `static/js/fairbet-ui.js` | Utilidades compartidas |
| `static/js/fairbet-home.js` | Lógica de la portada |
| `config/urls.py` | Rutas de páginas HTML |
| `docker-compose.yml`, `Dockerfile`, `.env.example`, `requirements.txt` | Infra |
| `docs/` | Guías y ADRs |
| `README.md` | Puerta de entrada del repo |

## Coordinación con otros integrantes

| Integrante | Módulo | Endpoints / archivos clave |
|------------|--------|---------------------------|
| 1 | Usuarios | `/api/users/`, `fairbet-cuenta.js` |
| 2 | Wallet | `/api/wallet/`, `fairbet-cartera.js` |
| 3 | Apuestas | `/api/bets/`, `fairbet-eventos.js`, `fairbet-apuestas.js` |
| 4 | Auditoría | `/api/operador/`, `fairbet-operador.js` |
| 5 | Frontend + entrega | Este checklist y layout general |

## Contacto del equipo

_Añade nombres, correos o canal de Discord/Slack del grupo._
