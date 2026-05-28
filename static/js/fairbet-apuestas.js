document.addEventListener("DOMContentLoaded", function () {
  const api = FairBetAPI;
  const ui = FairBetUI;
  const alerts = document.getElementById("apuestas-alerts");
  const tbody = document.getElementById("apuestas-tbody");
  const tbodyCombi = document.getElementById("combinadas-tbody");

  if (!ui.requireAuth("/apuestas/")) return;

  cargarApuestas();

  async function cargarApuestas() {
    tbody.innerHTML = '<tr><td colspan="7">Cargando…</td></tr>';
  tbodyCombi.innerHTML = '<tr><td colspan="5">Cargando…</td></tr>';
    try {
      const data = await api.myBets();
      const simples = data.simples || [];
      const combinadas = data.combinadas || [];

      if (!simples.length) {
        tbody.innerHTML =
          '<tr><td colspan="7" class="empty-state">Sin apuestas simples. <a href="/eventos/">Apostar</a></td></tr>';
      } else {
        tbody.innerHTML = "";
        simples.forEach(function (a) {
          const tr = document.createElement("tr");
          let accion = "—";
          if (a.cashout_disponible && a.cashout_estimado) {
            accion =
              '<button type="button" class="btn btn-sm btn-primary btn-cashout" data-id="' +
              a.id +
              '">Cash-out ~' +
              ui.formatSoles(a.cashout_estimado) +
              "</button>";
          }
          if (a.status === "cashout" && a.cashout_monto) {
            accion = "Cerrada: " + ui.formatSoles(a.cashout_monto);
          }
          tr.innerHTML =
            "<td>" +
            String(a.id).slice(0, 8) +
            "…</td><td>" +
            ui.escapeHtml(a.evento) +
            "</td><td>" +
            ui.escapeHtml(a.seleccion) +
            "</td><td>" +
            ui.formatSoles(a.stake) +
            "</td><td>" +
            a.odds_locked +
            '</td><td><span class="status-badge">' +
            ui.labelStatus(a.status) +
            "</span></td><td>" +
            accion +
            "</td>";
          tbody.appendChild(tr);
        });
        document.querySelectorAll(".btn-cashout").forEach(function (btn) {
          btn.addEventListener("click", async function () {
            if (!confirm("¿Confirmas cash-out anticipado?")) return;
            try {
              await api.cashout(btn.dataset.id);
              ui.showAlert(alerts, "Cash-out aplicado.", "success");
              ui.refreshHeaderSaldo();
              cargarApuestas();
            } catch (err) {
              ui.showAlert(alerts, err.message, "error");
            }
          });
        });
      }

      if (!combinadas.length) {
        tbodyCombi.innerHTML = '<tr><td colspan="5" class="empty-state">Sin combinadas.</td></tr>';
      } else {
        tbodyCombi.innerHTML = "";
        combinadas.forEach(function (c) {
          const piernas = (c.piernas || [])
            .map(function (p) {
              return p.evento + ": " + p.seleccion;
            })
            .join("; ");
          const tr = document.createElement("tr");
          tr.innerHTML =
            "<td>" +
            String(c.id).slice(0, 8) +
            "…</td><td>" +
            c.odds_locked +
            "</td><td>" +
            ui.formatFichas(c.stake) +
            '</td><td><span class="status-badge">' +
            ui.labelStatus(c.status) +
            "</span></td><td>" +
            ui.escapeHtml(piernas) +
            "</td>";
          tbodyCombi.appendChild(tr);
        });
      }
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  }
});
