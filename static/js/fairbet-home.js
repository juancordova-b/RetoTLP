/**
 * Página de inicio — Integrante 5.
 * Comprueba el API, muestra preview de eventos y adapta los botones al usuario.
 */
document.addEventListener("DOMContentLoaded", function () {
  const api = FairBetAPI;
  const ui = FairBetUI;

  comprobarApi();
  cargarPreviewEventos();
  adaptarBotonesSesion();
});

/** Pinta verde/rojo según responda /api/health/ */
async function comprobarApi() {
  const dot = document.getElementById("home-status-dot");
  const text = document.getElementById("home-status-text");
  if (!dot || !text) return;

  try {
    const data = await api.get("/api/health/");
    dot.classList.add("ok");
    text.textContent = "API en línea — " + (data.proyecto || "FairBet Lab");
  } catch {
    dot.classList.add("error");
    text.textContent = "API no disponible. ¿Está Docker en ejecución?";
  }
}

/** Muestra hasta 3 cuotas del primer mercado 1X2 disponible */
async function cargarPreviewEventos() {
  const listEl = document.getElementById("home-preview-list");
  const countEl = document.getElementById("home-preview-count");
  if (!listEl) return;

  try {
    const eventos = await api.get("/api/events/");
    const total = Array.isArray(eventos) ? eventos.length : 0;

    if (countEl) {
      countEl.textContent = total ? total + " evento(s)" : "Sin datos";
    }

    if (!total) {
      listEl.innerHTML =
        '<li class="ticket-empty">No hay eventos. Ejecuta: docker compose exec web python manage.py seed_demo</li>';
      return;
    }

    // Tomamos el primer evento que tenga mercado 1X2
    const evento = eventos.find(function (ev) {
      return ev.mercado_1x2 && ev.mercado_1x2.selecciones;
    });

    if (!evento || !evento.mercado_1x2) {
      listEl.innerHTML = '<li class="ticket-empty">Eventos sin mercado 1X2 cargado.</li>';
      return;
    }

    const selecciones = evento.mercado_1x2.selecciones.slice(0, 3);
    listEl.innerHTML = "";

    selecciones.forEach(function (sel) {
      const li = document.createElement("li");
      li.className = "home-preview-item";
      li.innerHTML =
        "<span>" +
        ui.escapeHtml(sel.etiqueta) +
        "</span><span>" +
        ui.escapeHtml(String(sel.odds)) +
        "</span>";
      listEl.appendChild(li);
    });
  } catch {
    listEl.innerHTML =
      '<li class="ticket-empty">No se pudieron cargar eventos. Revisa que el backend esté activo.</li>';
    if (countEl) countEl.textContent = "—";
  }
}

/** Si ya hay sesión, invita a Eventos en lugar de registrarse otra vez */
function adaptarBotonesSesion() {
  const cta = document.getElementById("home-cta");
  if (!cta || !api.isLoggedIn()) return;

  cta.innerHTML =
    '<a href="/eventos/" class="btn btn-primary">Ir a apostar</a>' +
    '<a href="/cartera/" class="btn btn-outline">Mi cartera</a>' +
    '<a href="/apuestas/" class="btn btn-outline">Mis apuestas</a>';
}
