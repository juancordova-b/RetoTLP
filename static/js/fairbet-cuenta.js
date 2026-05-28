document.addEventListener("DOMContentLoaded", function () {
  const api = FairBetAPI;
  const ui = FairBetUI;
  const alerts = document.getElementById("cuenta-alerts");
  const panelSesion = document.getElementById("panel-sesion");
  const panelPerfil = document.getElementById("panel-perfil");
  const perfilContent = document.getElementById("perfil-content");

  const params = new URLSearchParams(window.location.search);
  const nextUrl = params.get("next") || "/eventos/";

  if (api.isLoggedIn()) {
    redirigirOperadorSiCorresponde().then(function (redirigio) {
      if (redirigio) return;
      panelSesion.classList.add("hidden");
      panelPerfil.classList.remove("hidden");
      cargarPerfil();
    });
  }

  document.getElementById("form-registro").addEventListener("submit", async function (e) {
    e.preventDefault();
    ui.clearAlert(alerts);
    const fd = new FormData(e.target);
    try {
      const data = await api.register({
        username: fd.get("username"),
        email: fd.get("email"),
        password: fd.get("password"),
        dni: fd.get("dni"),
        dni_digito_verificador: fd.get("dni_digito_verificador"),
        fecha_nacimiento: fd.get("fecha_nacimiento"),
      });
      api.setToken(data.token, data.perfil.username);
      ui.showAlert(alerts, data.mensaje, "success");
      panelSesion.classList.add("hidden");
      panelPerfil.classList.remove("hidden");
      cargarPerfil();
      ui.refreshHeaderSaldo();
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  });

  document.getElementById("form-login").addEventListener("submit", async function (e) {
    e.preventDefault();
    ui.clearAlert(alerts);
    const fd = new FormData(e.target);
    try {
      const data = await api.login(fd.get("username"), fd.get("password"));
      api.setToken(data.token, fd.get("username"));
      ui.showAlert(alerts, "Sesión iniciada correctamente.", "success");
      const perfil = await api.me();
      window.location.href = perfil.es_staff ? "/operador/" : nextUrl;
    } catch (err) {
      ui.showAlert(alerts, "Usuario o contraseña incorrectos.", "error");
    }
  });

  async function redirigirOperadorSiCorresponde() {
    try {
      const perfil = await api.me();
      if (perfil.es_staff && window.location.pathname !== "/operador/") {
        window.location.href = "/operador/";
        return true;
      }
    } catch {
      /* si no hay perfil válido, cargarPerfil mostrará el error normal */
    }
    return false;
  }

  document.querySelectorAll(".btn-exclude").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      if (!confirm("¿Confirmas la autoexclusión? No podrás apostar ni recargar hasta que termine.")) {
        return;
      }
      ui.clearAlert(alerts);
      const payload = btn.dataset.indefinido
        ? { indefinido: true }
        : { dias: parseInt(btn.dataset.dias, 10) };
      try {
        const data = await api.selfExclude(payload);
        ui.showAlert(alerts, data.mensaje, "warning");
        cargarPerfil();
      } catch (err) {
        ui.showAlert(alerts, err.message, "error");
      }
    });
  });

  document.getElementById("form-limite").addEventListener("submit", async function (e) {
    e.preventDefault();
    ui.clearAlert(alerts);
    ui.clearAlert(document.getElementById("limite-alert"));
    const payload = {
      limite_deposito_diario: document.getElementById("limite-diario").value,
      limite_deposito_semanal: document.getElementById("limite-semanal").value,
      limite_deposito_mensual: document.getElementById("limite-mensual").value,
    };
    try {
      const data = await api.updateLimits(payload);
      const pendiente =
        data.perfil &&
        (data.perfil.limite_deposito_diario_pendiente ||
          data.perfil.limite_deposito_semanal_pendiente ||
          data.perfil.limite_deposito_mensual_pendiente);
      ui.showAlert(
        document.getElementById("limite-alert"),
        data.mensaje,
        pendiente ? "warning" : "success"
      );
      await cargarPerfil();
    } catch (err) {
      ui.showAlert(document.getElementById("limite-alert"), err.message, "error");
    }
  });

  document.getElementById("btn-verify-kyc").addEventListener("click", async function () {
    ui.clearAlert(alerts);
    try {
      const data = await api.verifyKyc();
      ui.showAlert(alerts, data.mensaje, "success");
      cargarPerfil();
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  });

  async function cargarPerfil() {
    try {
      const p = await api.me();
      const puede = p.puede_apostar ? "Sí" : "No";
      const statusClass = p.status.replace(/_/g, "_");

      document.getElementById("perfil-avatar").textContent = iniciales(p.username);
      document.getElementById("perfil-username").textContent = p.username;
      document.getElementById("perfil-email").textContent = p.email || "Sin correo";
      document.getElementById("perfil-status").innerHTML =
        '<span class="status-badge ' + statusClass + '">' + ui.labelStatus(p.status) + "</span>";

      const pendiente = renderPendientes(p);

      perfilContent.innerHTML =
        stat("DNI", p.dni ? p.dni + "-" + (p.dni_digito_verificador || "") : "—") +
        stat("Estado", ui.labelStatus(p.status)) +
        stat("Puede apostar", puede) +
        stat("Límite diario", ui.formatFichas(p.limite_diario_vigente)) +
        stat("Límite semanal", ui.formatFichas(p.limite_semanal_vigente)) +
        stat("Límite mensual", ui.formatFichas(p.limite_mensual_vigente)) +
        stat("Autoexcluido", p.esta_autoexcluido ? "Sí" : "No") +
        pendiente;

      document.getElementById("limite-diario").value = formatInputMoney(
        p.limite_diario_vigente
      );
      document.getElementById("limite-semanal").value = formatInputMoney(
        p.limite_semanal_vigente
      );
      document.getElementById("limite-mensual").value = formatInputMoney(
        p.limite_mensual_vigente
      );

      const btnKyc = document.getElementById("btn-verify-kyc");
      const kycAlert = document.getElementById("kyc-alert");
      if (p.status === "verificado" && !p.esta_autoexcluido) {
        btnKyc.disabled = true;
        btnKyc.textContent = "Cuenta ya verificada";
        kycAlert.className = "alert alert-success";
        kycAlert.innerHTML = "<strong>Cuenta verificada.</strong> Ya puedes apostar y usar tu cartera virtual.";
      } else if (p.esta_autoexcluido) {
        btnKyc.disabled = true;
        kycAlert.className = "alert alert-warning";
        kycAlert.innerHTML = "<strong>Autoexclusión activa.</strong> No podrás apostar ni recargar hasta que termine.";
      } else {
        btnKyc.disabled = false;
        btnKyc.textContent = "Verificar KYC (demo)";
        kycAlert.className = "alert alert-warning";
        kycAlert.innerHTML =
          'Para apostar debes estar <strong>verificado</strong>. En la demo puedes simularlo con el botón siguiente.';
      }
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  }

  function stat(label, value) {
    return (
      '<div class="account-stat"><span>' +
      label +
      "</span><strong>" +
      value +
      "</strong></div>"
    );
  }

  function iniciales(username) {
    return (username || "AP").slice(0, 2).toUpperCase();
  }

  function renderPendientes(p) {
    const rows = [];
    if (p.limite_deposito_diario_pendiente) {
      rows.push(
        "Diario: " +
          ui.formatFichas(p.limite_deposito_diario_pendiente) +
          " desde " +
          ui.formatDate(p.limite_efectivo_desde)
      );
    }
    if (p.limite_deposito_semanal_pendiente) {
      rows.push(
        "Semanal: " +
          ui.formatFichas(p.limite_deposito_semanal_pendiente) +
          " desde " +
          ui.formatDate(p.limite_semanal_efectivo_desde)
      );
    }
    if (p.limite_deposito_mensual_pendiente) {
      rows.push(
        "Mensual: " +
          ui.formatFichas(p.limite_deposito_mensual_pendiente) +
          " desde " +
          ui.formatDate(p.limite_mensual_efectivo_desde)
      );
    }
    if (!rows.length) return "";
    return stat("Aumentos pendientes", rows.join("<br>"));
  }

  function formatInputMoney(value) {
    const n = parseFloat(value);
    if (Number.isNaN(n)) return "";
    return n.toFixed(2);
  }
});
