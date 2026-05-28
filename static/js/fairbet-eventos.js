document.addEventListener("DOMContentLoaded", function () {
  const api = FairBetAPI;
  const ui = FairBetUI;
  const alerts = document.getElementById("eventos-alerts");
  const listEl = document.getElementById("eventos-list");

  let modo = "simple";
  let seleccionActual = null;
  const piernasCombi = [];
  const sockets = {};
  let saldoActual = 0;

  const els = {
    saldoBanner: document.getElementById("saldo-banner"),
    saldoEventos: document.getElementById("saldo-eventos"),
    saldoAviso: document.getElementById("saldo-aviso"),
    tabSimple: document.getElementById("tab-simple"),
    tabCombi: document.getElementById("tab-combi"),
    slipModoText: document.getElementById("slip-modo-text"),
    slipSimple: document.getElementById("slip-simple"),
    slipCombi: document.getElementById("slip-combi"),
    combiLegs: document.getElementById("combi-legs"),
    combiEmpty: document.getElementById("combi-empty"),
    formCombi: document.getElementById("form-combinada"),
    combiOdds: document.getElementById("combi-odds"),
    combiPayout: document.getElementById("combi-payout"),
    combiPayoutRow: document.getElementById("combi-payout-row"),
    stakeCombi: document.getElementById("stake-combi"),
  };

  initModoTabs();
  initModal();
  initCombiForm();
  restaurarBoletoGuardado();

  if (!api.isLoggedIn()) {
    ui.showAlert(
      alerts,
      "Puedes revisar partidos y cuotas como invitado. Para apostar, entra o regístrate.",
      "info"
    );
    document.getElementById("step-2").classList.add("steps-active");
    cargarEventos();
  } else {
    cargarSaldo();
    cargarEventos();
  }

  document.getElementById("stake-combi").addEventListener("input", function () {
    guardarCombi();
    renderCombi();
  });
  document.getElementById("stake-input").addEventListener("input", actualizarPayoutModal);

  function initModoTabs() {
    document.querySelectorAll(".mode-tab").forEach(function (tab) {
      tab.addEventListener("click", function () {
        modo = tab.dataset.mode;
        document.querySelectorAll(".mode-tab").forEach(function (t) {
          t.classList.toggle("active", t === tab);
        });
        els.slipSimple.classList.toggle("hidden", modo !== "simple");
        els.slipCombi.classList.toggle("hidden", modo !== "combi");
        if (modo === "simple") {
          els.slipModoText.textContent =
            "Haz clic en una cuota (botón con número verde) para apostar a ese resultado.";
        } else {
          els.slipModoText.textContent =
            "Combina 2 o más mercados: pueden ser del mismo partido (ej. gana Perú + menos 2.5 goles).";
        }
        listEl.querySelectorAll(".odds-btn").forEach(function (btn) {
          btn.classList.remove("selected", "in-combi");
        });
        if (modo === "combi") renderCombi();
      });
    });
  }

  function initModal() {
    document.getElementById("btn-cerrar-modal").addEventListener("click", cerrarModal);
    document.getElementById("modal-overlay").addEventListener("click", function (e) {
      if (e.target.id === "modal-overlay") cerrarModal();
    });
    document.getElementById("form-apuesta").addEventListener("submit", function (e) {
      e.preventDefault();
      enviarApuestaSimple(false);
    });
  }

  function initCombiForm() {
    document.getElementById("form-combinada").addEventListener("submit", async function (e) {
      e.preventDefault();
      if (!requiereSesion()) return;
      if (saldoActual <= 0) {
        ui.showAlert(
          alerts,
          "Sin saldo. Ve a Cartera (menú arriba) y recarga soles virtuales primero.",
          "warning"
        );
        return;
      }
      if (piernasCombi.length < 2) {
        ui.showAlert(alerts, "Necesitas al menos 2 selecciones en el boleto.", "error");
        return;
      }
      try {
        const data = await api.placeCombined({
          selection_ids: piernasCombi.map(function (p) {
            return p.selectionId;
          }),
          stake: els.stakeCombi.value,
        });
        piernasCombi.length = 0;
        ui.clearSlip();
        renderCombi();
        marcarSeleccionesEnDom();
        ui.showAlert(
          alerts,
          "¡Combinada registrada! Cuota " + data.combinada.odds_locked,
          "success"
        );
        ui.refreshHeaderSaldo();
        cargarSaldo();
      } catch (err) {
        ui.showAlert(alerts, err.message, "error");
      }
    });
    document.getElementById("btn-limpiar-combi").addEventListener("click", function () {
      piernasCombi.length = 0;
      ui.clearSlip();
      renderCombi();
      marcarSeleccionesEnDom();
    });
  }

  async function cargarSaldo() {
    if (!api.isLoggedIn()) return;
    try {
      const data = await api.balance();
      saldoActual = parseFloat(data.saldo_fichas) || 0;
      els.saldoEventos.textContent = ui.formatSoles(data.saldo_fichas);
      els.saldoBanner.classList.remove("hidden");
      document.getElementById("step-1").classList.toggle("steps-done", saldoActual > 0);
      document.getElementById("step-1").classList.toggle("steps-active", saldoActual <= 0);
      if (saldoActual <= 0) {
        els.saldoBanner.classList.add("saldo-bajo");
        els.saldoAviso.textContent = "Sin saldo no puedes apostar. Recarga en Cartera.";
        els.saldoAviso.classList.remove("hidden");
      } else {
        els.saldoBanner.classList.remove("saldo-bajo");
        els.saldoAviso.classList.add("hidden");
      }
    } catch {
      /* ignore */
    }
  }

  function requiereSesion() {
    if (!api.isLoggedIn()) {
      window.location.href = "/cuenta/?next=/eventos/";
      return false;
    }
    return true;
  }

  async function enviarApuestaSimple(confirmarRequote, oddsEsperada) {
    if (!requiereSesion()) return;
    if (saldoActual <= 0) {
      ui.showAlert(
        document.getElementById("modal-alerts"),
        "Sin saldo. Recarga en Cartera antes de apostar.",
        "error"
      );
      return;
    }
    const modalAlerts = document.getElementById("modal-alerts");
    ui.clearAlert(modalAlerts);
    const payload = {
      event_id: seleccionActual.eventId,
      selection_id: seleccionActual.selectionId,
      stake: document.getElementById("stake-input").value,
      odds_esperada: oddsEsperada || seleccionActual.odds,
      confirmar_requote: confirmarRequote,
    };
    try {
      await api.placeBet(payload);
      cerrarModal();
      ui.clearSlip();
      ui.showAlert(alerts, "¡Apuesta registrada! Revisa en Mis apuestas.", "success");
      ui.refreshHeaderSaldo();
      cargarSaldo();
      document.getElementById("step-3").classList.add("steps-done");
    } catch (err) {
      if (err.status === 409 && err.data && err.data.requiere_reconfirmacion) {
        const ok = confirm(
          "La cuota cambió a " + err.data.nueva_cuota + ". ¿Apostar con la nueva cuota?"
        );
        if (ok) await enviarApuestaSimple(true, err.data.nueva_cuota);
        return;
      }
      ui.showAlert(modalAlerts, err.message, "error");
    }
  }

  async function cargarEventos() {
    listEl.innerHTML = '<p class="empty-state">Cargando partidos…</p>';
    try {
      const eventos = await api.events();
      listEl.innerHTML = "";
      if (!eventos.length) {
        listEl.innerHTML =
          '<p class="empty-state">No hay partidos. Ejecuta <code>seed_demo</code> en Docker.</p>';
        return;
      }
      eventos.forEach(function (ev) {
        listEl.appendChild(crearTarjetaEvento(ev));
        if (puedeApostarEvento(ev.status)) conectarWs(ev.id);
      });
      limpiarBoletoSiEventoNoExiste(eventos);
      sincronizarBoletoConEventos(eventos);
      marcarSeleccionesEnDom();
      destacarEventoDesdeUrl();
      document.getElementById("step-2").classList.add("steps-active");
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  }

  function puedeApostarEvento(status) {
    return status === "programado" || status === "en_vivo";
  }

  function marcadorEvento(ev) {
    const gl = Number(ev.goles_local || 0);
    const gv = Number(ev.goles_visitante || 0);
    return "Marcador: " + gl + " - " + gv;
  }

  function crearTarjetaEvento(ev) {
    const card = document.createElement("article");
    card.className = "event-card";
    card.dataset.eventId = ev.id;

    const puede = puedeApostarEvento(ev.status);
    card.innerHTML =
      '<div class="event-header">' +
      '<div><div class="event-teams">' +
      ui.escapeHtml(ev.equipo_local) +
      " vs " +
      ui.escapeHtml(ev.equipo_visitante) +
      '</div><div class="event-score">' +
      marcadorEvento(ev) +
      '</div><div class="event-meta">' +
      ui.formatDate(ev.inicio_programado) +
      '</div></div><span class="status-badge ' +
      ev.status +
      '">' +
      ui.labelStatus(ev.status) +
      "</span></div>" +
      (puede
        ? ""
        : '<p class="form-hint market-hint">Este partido no acepta apuestas ahora.</p>');

    const mercadosOrden = ordenarMercados(ev.mercados || []);
    mercadosOrden.forEach(function (mercado) {
      card.appendChild(crearBloqueMercado(ev, mercado, puede));
    });

    return card;
  }

  function ordenarMercados(mercados) {
    const orden = { "1X2": 0, OU25: 1, BTTS: 2, AH: 3 };
    return mercados.slice().sort(function (a, b) {
      return (orden[a.tipo] ?? 9) - (orden[b.tipo] ?? 9);
    });
  }

  function hintMercado(tipo) {
    const hints = {
      "1X2": "¿Quién gana? Local · Empate · Visitante",
      OU25: "¿Habrá más o menos de 2.5 goles?",
      BTTS: "¿Anotan los dos equipos?",
      AH: "Ventaja de goles (hándicap)",
    };
    return hints[tipo] || "";
  }

  function crearBloqueMercado(ev, mercado, eventoPuede) {
    const block = document.createElement("div");
    block.className = "market-block";
    const suspendido = !mercado.disponible;

    block.innerHTML =
      '<div class="market-head">' +
      "<strong>" +
      ui.escapeHtml(mercado.nombre) +
      "</strong>" +
      (suspendido ? '<span class="badge-suspendido">Suspendido</span>' : "") +
      "</div>" +
      '<p class="form-hint market-hint">' +
      hintMercado(mercado.tipo) +
      "</p>";

    const row = document.createElement("div");
    const cols = (mercado.selecciones || []).length;
    row.className = "odds-row" + (cols === 2 ? " odds-row-2" : "");

    (mercado.selecciones || []).forEach(function (sel) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "odds-btn";
      btn.dataset.eventId = ev.id;
      btn.dataset.mercadoId = mercado.id;
      btn.dataset.selectionId = sel.id;
      btn.dataset.odds = sel.odds;
      btn.dataset.label = sel.etiqueta;

      const puede =
        eventoPuede && sel.activo && mercado.disponible && sel.mercado_disponible !== false;
      btn.disabled = !puede;

      btn.innerHTML =
        '<span class="odds-label">' +
        ui.escapeHtml(sel.etiqueta) +
        '</span><span class="odds-value" data-odds-for="' +
        sel.id +
        '">' +
        sel.odds +
        "</span>";

      btn.addEventListener("click", function () {
        onCuotaClick(ev, sel, mercado, btn);
      });

      row.appendChild(btn);
    });

    block.appendChild(row);
    return block;
  }

  function onCuotaClick(ev, sel, mercado, btn) {
    if (!requiereSesion()) return;

    if (modo === "combi") {
      agregarCombi(ev, sel, mercado, btn);
      return;
    }

    abrirModal(ev, sel);
    guardarSimple(ev, sel, mercado);
    renderSimpleSlip(ui.readSavedSlip().simple);
    listEl.querySelectorAll(".odds-btn").forEach(function (b) {
      b.classList.remove("selected");
    });
    btn.classList.add("selected");
  }

  function agregarCombi(ev, sel, mercado, btn) {
    if (
      piernasCombi.some(function (p) {
        return p.mercadoId === mercado.id;
      })
    ) {
      ui.showAlert(
        alerts,
        "Solo una opción por mercado. Quita la anterior del boleto.",
        "warning"
      );
      return;
    }
    if (
      piernasCombi.some(function (p) {
        return p.selectionId === sel.id;
      })
    ) {
      return;
    }
    const pick =
      mercado.tipo !== "1X2"
        ? mercado.nombre + " · " + sel.etiqueta
        : sel.etiqueta;
    piernasCombi.push({
      eventId: ev.id,
      mercadoId: mercado.id,
      selectionId: sel.id,
      label: ev.equipo_local + " vs " + ev.equipo_visitante,
      pick: pick,
      odds: parseFloat(sel.odds),
    });
    guardarCombi();
    renderCombi();
    marcarSeleccionesEnDom();
    document.getElementById("bet-slip").scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function marcarSeleccionesEnDom() {
    listEl.querySelectorAll(".odds-btn").forEach(function (btn) {
      const sid = parseInt(btn.dataset.selectionId, 10);
      const enCombi = piernasCombi.some(function (p) {
        return p.selectionId === sid;
      });
      btn.classList.toggle("in-combi", enCombi && modo === "combi");
    });
  }

  function renderCombi() {
    els.combiLegs.innerHTML = "";
    let producto = 1;
    piernasCombi.forEach(function (p) {
      producto *= p.odds;
      const li = document.createElement("li");
      li.className = "combi-leg-item";
      li.innerHTML =
        "<span><strong>" +
        ui.escapeHtml(p.label) +
        "</strong><br><small>" +
        ui.escapeHtml(p.pick) +
        " @ " +
        p.odds +
        "</small></span>" +
        '<button type="button" class="btn-remove-leg" data-sid="' +
        p.selectionId +
        '" aria-label="Quitar">×</button>';
      li.querySelector(".btn-remove-leg").addEventListener("click", function () {
        const sid = parseInt(li.querySelector(".btn-remove-leg").dataset.sid, 10);
        const idx = piernasCombi.findIndex(function (x) {
          return x.selectionId === sid;
        });
        if (idx >= 0) piernasCombi.splice(idx, 1);
        guardarCombi();
        renderCombi();
        marcarSeleccionesEnDom();
      });
      els.combiLegs.appendChild(li);
    });

    const listo = piernasCombi.length >= 2;
    els.combiEmpty.classList.toggle("hidden", listo);
    els.formCombi.classList.toggle("hidden", !listo);
    els.combiOdds.textContent = piernasCombi.length ? producto.toFixed(2) : "—";

    const stake = parseFloat(els.stakeCombi.value) || 0;
    if (listo && stake > 0) {
      const payout = stake * producto;
      els.combiPayout.textContent = ui.formatSoles(payout);
      els.combiPayoutRow.classList.remove("hidden");
    } else {
      els.combiPayoutRow.classList.add("hidden");
    }
  }

  function abrirModal(ev, sel) {
    seleccionActual = {
      eventId: ev.id,
      selectionId: sel.id,
      odds: sel.odds,
      etiqueta: sel.etiqueta,
    };
    document.getElementById("modal-partido").textContent =
      ev.equipo_local + " vs " + ev.equipo_visitante;
    document.getElementById("modal-seleccion").textContent = sel.etiqueta;
    document.getElementById("modal-cuota").textContent = sel.odds;
    document.getElementById("stake-input").value = "10.00";
    document.getElementById("modal-alerts").innerHTML = "";
    actualizarPayoutModal();
    document.getElementById("modal-overlay").classList.remove("hidden");
  }

  function actualizarPayoutModal() {
    if (!seleccionActual) return;
    const stake = parseFloat(document.getElementById("stake-input").value) || 0;
    const odds = parseFloat(seleccionActual.odds) || 0;
    const payout = stake * odds;
    document.getElementById("modal-payout").textContent = ui.formatSoles(payout);
  }

  function cerrarModal() {
    document.getElementById("modal-overlay").classList.add("hidden");
    seleccionActual = null;
  }

  function guardarSimple(ev, sel, mercado) {
    ui.saveSlip({
      mode: "simple",
      simple: {
        eventId: ev.id,
        mercadoId: mercado.id,
        selectionId: sel.id,
        label: ev.equipo_local + " vs " + ev.equipo_visitante,
        pick: sel.etiqueta,
        odds: parseFloat(sel.odds),
      },
    });
  }

  function guardarCombi() {
    if (!piernasCombi.length) {
      ui.clearSlip();
      return;
    }
    ui.saveSlip({ mode: "combi", legs: piernasCombi, stake: els.stakeCombi.value });
  }

  function restaurarBoletoGuardado() {
    const slip = ui.readSavedSlip();
    if (!slip) return;
    if (slip.mode === "combi" && Array.isArray(slip.legs)) {
      modo = "combi";
      piernasCombi.length = 0;
      slip.legs.forEach(function (leg) {
        piernasCombi.push(leg);
      });
      document.querySelectorAll(".mode-tab").forEach(function (tab) {
        const active = tab.dataset.mode === "combi";
        tab.classList.toggle("active", active);
      });
      els.slipSimple.classList.add("hidden");
      els.slipCombi.classList.remove("hidden");
      els.slipModoText.textContent =
        "Boleto restaurado. Puedes confirmar, quitar selecciones o seguir agregando mercados.";
      if (slip.stake) els.stakeCombi.value = slip.stake;
      renderCombi();
    } else if (slip.mode === "simple" && slip.simple) {
      renderSimpleSlip(slip.simple);
    }
  }

  function renderSimpleSlip(simple) {
    els.slipSimple.innerHTML =
      '<div class="slip-summary">' +
      "<div><span>Partido</span><strong>" +
      ui.escapeHtml(simple.label) +
      "</strong></div>" +
      "<div><span>Selección</span><strong>" +
      ui.escapeHtml(simple.pick) +
      "</strong></div>" +
      "<div><span>Cuota</span><strong>" +
      Number(simple.odds).toFixed(2) +
      "</strong></div></div>" +
      '<button type="button" id="btn-simple-restaurar" class="btn btn-primary btn-block">Continuar apuesta</button>' +
      '<button type="button" id="btn-simple-quitar" class="btn btn-outline btn-block">Quitar boleto</button>';

    document.getElementById("btn-simple-quitar").addEventListener("click", function () {
      ui.clearSlip();
      els.slipSimple.innerHTML =
        '<p class="slip-empty">Aún no elegiste ninguna cuota.<br>Selecciona una opción en un partido.</p>';
      marcarSeleccionesEnDom();
    });

    document.getElementById("btn-simple-restaurar").addEventListener("click", async function () {
      const eventos = await api.events();
      const ev = eventos.find(function (x) {
        return x.id === simple.eventId;
      });
      if (!ev || !puedeApostarEvento(ev.status)) {
        ui.showAlert(alerts, "Ese evento ya no acepta apuestas. Quita el boleto.", "warning");
        return;
      }
      const mercado = (ev.mercados || []).find(function (m) {
        return m.id === simple.mercadoId;
      });
      const sel = mercado && (mercado.selecciones || []).find(function (s) {
        return s.id === simple.selectionId;
      });
      if (!sel) {
        ui.showAlert(alerts, "La selección ya no está disponible.", "warning");
        return;
      }
      abrirModal(ev, sel);
    });
  }

  function limpiarBoletoSiEventoNoExiste(eventos) {
    const idsVigentes = new Set(
      eventos.filter(function (ev) {
        return puedeApostarEvento(ev.status);
      }).map(function (ev) {
        return ev.id;
      })
    );
    const slip = ui.readSavedSlip();
    if (!slip) return;
    if (slip.mode === "simple" && slip.simple && !idsVigentes.has(slip.simple.eventId)) {
      ui.clearSlip();
    }
    if (slip.mode === "combi" && Array.isArray(slip.legs)) {
      const legs = slip.legs.filter(function (leg) {
        return idsVigentes.has(leg.eventId);
      });
      if (legs.length !== slip.legs.length) {
        piernasCombi.length = 0;
        legs.forEach(function (leg) {
          piernasCombi.push(leg);
        });
        guardarCombi();
        renderCombi();
      }
    }
  }

  function buscarSeleccionEnEventos(eventos, selectionId) {
    for (const ev of eventos) {
      for (const mercado of ev.mercados || []) {
        const sel = (mercado.selecciones || []).find(function (s) {
          return s.id === selectionId;
        });
        if (sel) return { ev: ev, mercado: mercado, sel: sel };
      }
    }
    return null;
  }

  function sincronizarBoletoConEventos(eventos) {
    const slip = ui.readSavedSlip();
    if (!slip) return;

    if (slip.mode === "simple" && slip.simple) {
      const encontrado = buscarSeleccionEnEventos(eventos, slip.simple.selectionId);
      if (!encontrado) return;
      slip.simple.odds = parseFloat(encontrado.sel.odds);
      slip.simple.pick = encontrado.sel.etiqueta;
      ui.saveSlip(slip);
      renderSimpleSlip(slip.simple);
    }

    if (slip.mode === "combi" && Array.isArray(slip.legs)) {
      let cambio = false;
      piernasCombi.forEach(function (leg) {
        const encontrado = buscarSeleccionEnEventos(eventos, leg.selectionId);
        if (!encontrado) return;
        const nuevaCuota = parseFloat(encontrado.sel.odds);
        if (leg.odds !== nuevaCuota) {
          leg.odds = nuevaCuota;
          leg.pick =
            encontrado.mercado.tipo !== "1X2"
              ? encontrado.mercado.nombre + " · " + encontrado.sel.etiqueta
              : encontrado.sel.etiqueta;
          cambio = true;
        }
      });
      if (cambio) {
        guardarCombi();
        renderCombi();
      }
    }
  }

  function actualizarBoletoPorCuota(selectionId, odds) {
    const nuevaCuota = parseFloat(odds);
    if (!Number.isFinite(nuevaCuota)) return;
    const slip = ui.readSavedSlip();
    if (!slip) return;

    if (slip.mode === "simple" && slip.simple && slip.simple.selectionId === selectionId) {
      slip.simple.odds = nuevaCuota;
      ui.saveSlip(slip);
      renderSimpleSlip(slip.simple);
    }

    if (slip.mode === "combi") {
      let cambio = false;
      piernasCombi.forEach(function (leg) {
        if (leg.selectionId === selectionId) {
          leg.odds = nuevaCuota;
          cambio = true;
        }
      });
      if (cambio) {
        guardarCombi();
        renderCombi();
      }
    }
  }

  function destacarEventoDesdeUrl() {
    const params = new URLSearchParams(window.location.search);
    const eventId = params.get("evento");
    if (!eventId) return;
    const card = listEl.querySelector('[data-event-id="' + eventId + '"]');
    if (!card) return;
    card.classList.add("event-card-highlight");
    card.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function conectarWs(eventoId) {
    if (sockets[eventoId]) return;
    const host = window.location.hostname || "localhost";
    const ws = new WebSocket("ws://" + host + ":8001/ws/eventos/" + eventoId + "/odds/");
    sockets[eventoId] = ws;
    ws.onmessage = function (msg) {
      try {
        const data = JSON.parse(msg.data);
        if (data.tipo === "odds_update" && data.selection_id) {
          document.querySelectorAll('[data-odds-for="' + data.selection_id + '"]').forEach(function (el) {
            el.textContent = data.odds;
          });
          actualizarBoletoPorCuota(data.selection_id, data.odds);
        }
        if (data.tipo === "mercado_suspendido") {
          ui.showAlert(alerts, "Mercado pausado unos segundos (partido en vivo).", "warning");
          setTimeout(cargarEventos, (data.segundos || 30) * 1000);
        }
        if (data.tipo === "gol") {
          ui.showAlert(
            alerts,
            "Gol de " + data.equipo_gol + ". " + data.marcador + ". Mercado pausado temporalmente.",
            "warning"
          );
          cargarEventos();
        }
        if (data.tipo === "evento_critico") {
          ui.showAlert(
            alerts,
            data.descripcion + ". Mercado pausado temporalmente por revisión de cuotas.",
            "warning"
          );
          cargarEventos();
        }
      } catch (e) {
        /* ignore */
      }
    };
  }
});
