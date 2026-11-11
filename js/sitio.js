/* El Cocinerito · comportamiento del sitio (sin dependencias) */
(function () {
  var D = window.COCINERITO || {};
  var reducido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* menú móvil */
  var boton = document.querySelector(".abrir-menu");
  var menu = document.getElementById("menu");
  if (boton && menu) {
    boton.addEventListener("click", function () {
      var abierto = menu.classList.toggle("abierto");
      boton.setAttribute("aria-expanded", abierto ? "true" : "false");
    });
  }

  /* entradas al hacer scroll */
  var piezas = document.querySelectorAll(".aparece");
  if ("IntersectionObserver" in window && !reducido) {
    var io = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("visto"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    piezas.forEach(function (p) { io.observe(p); });
  } else {
    piezas.forEach(function (p) { p.classList.add("visto"); });
  }

  /* inicio: líneas; el fondo y la figura cambian con la línea activa */
  var secLineas = document.querySelector("[data-lineas]");
  if (secLineas) {
    var enlL = secLineas.querySelectorAll(".lineas__lista a");
    var figs = secLineas.querySelectorAll(".lineas__fig");
    var activar = function (i) {
      enlL.forEach(function (a) {
        var si = a.getAttribute("data-linea-i") === i;
        a.classList.toggle("activo", si);
        if (si) { var li = a.parentNode; ["--c", "--acento", "--tinte"].forEach(function (k) { secLineas.style.setProperty(k, li.style.getPropertyValue(k)); }); }
      });
      figs.forEach(function (f) { f.classList.toggle("ver", f.getAttribute("data-linea-i") === i); });
    };
    enlL.forEach(function (a) {
      var i = a.getAttribute("data-linea-i");
      a.addEventListener("mouseenter", function () { activar(i); });
      a.addEventListener("focus", function () { activar(i); });
    });
    activar("0");
  }

  /* profundidad: el personaje y los productos se mueven un poco con el cursor y el scroll */
  var capas = document.querySelectorAll("[data-prof]");
  if (capas.length && !reducido) {
    var mx = 0, my = 0, pendiente = false;
    var pintar = function () {
      pendiente = false;
      capas.forEach(function (c) {
        var k = parseFloat(c.getAttribute("data-prof")) || 0;
        var r = c.getBoundingClientRect();
        var centro = (r.top + r.height / 2 - innerHeight / 2) / innerHeight;
        c.style.setProperty("--px", (mx * 14 * k).toFixed(1) + "px");
        c.style.setProperty("--py", (my * 10 * k - centro * 36 * k).toFixed(1) + "px");
      });
    };
    var pedir = function () { if (!pendiente) { pendiente = true; requestAnimationFrame(pintar); } };
    if (window.matchMedia("(hover: hover)").matches) {
      window.addEventListener("pointermove", function (ev) { mx = ev.clientX / innerWidth - 0.5; my = ev.clientY / innerHeight - 0.5; pedir(); }, { passive: true });
    }
    window.addEventListener("scroll", pedir, { passive: true });
    pintar();
  }

  /* riel del portafolio: se puede arrastrar con el mouse */
  document.querySelectorAll("[data-riel]").forEach(function (riel) {
    var x0 = 0, s0 = 0, abajo = false, movio = false;
    riel.addEventListener("pointerdown", function (ev) { if (ev.pointerType !== "mouse") return; abajo = true; movio = false; x0 = ev.clientX; s0 = riel.scrollLeft; });
    window.addEventListener("pointermove", function (ev) {
      if (!abajo) return;
      var d = ev.clientX - x0;
      if (Math.abs(d) > 5) { movio = true; riel.classList.add("arrastrando"); }
      riel.scrollLeft = s0 - d;
    });
    window.addEventListener("pointerup", function () { abajo = false; riel.classList.remove("arrastrando"); });
    riel.addEventListener("click", function (ev) { if (movio) { ev.preventDefault(); ev.stopPropagation(); movio = false; } }, true);
  });

  /* ventana de detalle: al hacer clic en un producto se ven sus presentaciones */
  var dlg = document.getElementById("dialogo");
  var fams = {};
  (D.familias || []).forEach(function (f) { fams[f.id] = f; });
  var lineas = {};
  (D.lineas || []).forEach(function (l) { lineas[l.id] = l; });
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var nombrePres = {};
  (D.presentaciones || []).forEach(function (p) { nombrePres[p.id] = p.nombre; });
  if (dlg && typeof dlg.showModal === "function") {
    var abrir = function (f, origen) {
      var l = lineas[f.linea];
      ["--c", "--acento", "--tinte"].forEach(function (k, j) { dlg.style.setProperty(k, [l.color, l.acento, l.tinte][j]); });
      dlg.querySelector("[data-dlg-foto]").innerHTML = f.foto
        ? '<img src="' + esc(f.foto) + '" alt="' + esc(f.nombre) + ' El Cocinerito">'
        : '<span class="sin-foto">' + (D.bolsa || "") + "<span>Foto por cargar</span></span>";
      dlg.querySelector("[data-dlg-linea]").innerHTML = '<i class="punto" style="--c:' + l.color + (l.borde ? ";--b:" + l.borde : "") + '" aria-hidden="true"></i>' + esc(l.nombre);
      dlg.querySelector("[data-dlg-nombre]").textContent = f.nombre;
      dlg.querySelector("[data-dlg-variantes]").innerHTML = '<ul class="variantes">' + f.variantes.map(function (v) {
        var g = v.gramajes.length ? v.gramajes.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") : '<li><span class="pendiente">Por confirmar</span></li>';
        return '<li class="variante"><span class="variante__tipo">' + (v.forma ? "<strong>" + esc(v.forma) + "</strong> · " : "") + esc(v.envase) + '</span><ul class="gramajes">' + g + "</ul></li>";
      }).join("") + "</ul>";
      dlg._origen = origen;
      dlg.showModal();
    };
    document.addEventListener("click", function (ev) {
      var a = ev.target.closest("a[data-familia]");
      if (!a || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button !== 0) return;
      var f = fams[a.getAttribute("data-familia")];
      if (!f) return;
      ev.preventDefault();
      abrir(f, a);
    });
    dlg.addEventListener("click", function (ev) { if (ev.target === dlg || ev.target.closest("[data-cerrar]")) dlg.close(); });
    dlg.addEventListener("close", function () { if (dlg._origen) dlg._origen.focus(); });
  }

  /* WhatsApp: el tipo de negocio elegido define el mensaje */
  document.querySelectorAll("[data-wa-form]").forEach(function (form) {
    var salida = form.querySelector("[data-wa-texto]");
    var enlace = form.querySelector("[data-wa-enlace]");
    var numero = (D.empresa && D.empresa.whatsapp) || "";
    var componer = function () {
      var elegido = form.querySelector("input[name=perfil]:checked");
      var p = (D.perfiles || []).filter(function (x) { return elegido && x.id === elegido.value; })[0];
      var texto = p ? p.mensaje : "Hola, quiero información sobre los productos El Cocinerito.";
      salida.textContent = texto;
      enlace.href = "https://wa.me/" + numero + "?text=" + encodeURIComponent(texto);
    };
    form.addEventListener("change", componer);
    form.addEventListener("submit", function (ev) { ev.preventDefault(); });
    componer();
  });

  /* catálogo: filtros por línea, presentación y búsqueda */
  var rejilla = document.getElementById("rejilla");
  var filtros = document.getElementById("filtros");
  if (rejilla && filtros) {
    var qs = new URLSearchParams(location.search);
    var hashLinea = (location.hash.match(/^#linea-(.+)$/) || [])[1] || "";
    var estado = { linea: qs.get("linea") || hashLinea, presentacion: qs.get("presentacion") || "", q: "" };
    var buscar = document.getElementById("buscar");
    var contador = document.getElementById("contador");
    var vacio = document.getElementById("vacio");
    var normal = function (s) { return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); };
    var aplicar = function () {
      filtros.querySelectorAll("[data-linea]").forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-linea") === estado.linea ? "true" : "false"); });
      filtros.querySelectorAll("[data-presentacion]").forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-presentacion") === estado.presentacion ? "true" : "false"); });
      var n = 0;
      rejilla.querySelectorAll("li").forEach(function (li) {
        var ok = (!estado.linea || li.dataset.linea === estado.linea) &&
                 (!estado.presentacion || (" " + li.dataset.presentaciones + " ").indexOf(" " + estado.presentacion + " ") > -1) &&
                 (!estado.q || normal(li.dataset.nombre).indexOf(normal(estado.q)) > -1);
        li.hidden = !ok;
        if (ok) n++;
      });
      rejilla.querySelectorAll("[data-grupo]").forEach(function (g) {
        g.hidden = !g.querySelector("li:not([hidden])");
      });
      contador.textContent = n === 1 ? "1 producto" : n + " productos";
      rejilla.querySelectorAll("[data-grupo]:not([hidden])").forEach(function (g, j) { g.classList.toggle("grupo--par", j % 2 === 1); });
      vacio.hidden = n > 0;
      try {
        var url = new URL(location.href);
        ["linea", "presentacion"].forEach(function (k) { if (estado[k]) url.searchParams.set(k, estado[k]); else url.searchParams.delete(k); });
        history.replaceState(null, "", url);
      } catch (err) { /* sin historial disponible */ }
    };
    filtros.addEventListener("click", function (ev) {
      var b = ev.target.closest("button");
      if (!b) return;
      if (b.hasAttribute("data-linea")) estado.linea = b.getAttribute("data-linea");
      if (b.hasAttribute("data-presentacion")) estado.presentacion = b.getAttribute("data-presentacion");
      aplicar();
      if (b.hasAttribute("data-linea")) { var top = rejilla.getBoundingClientRect().top + scrollY - filtros.offsetHeight - 70; if (scrollY > top) window.scrollTo({ top: top, behavior: reducido ? "auto" : "smooth" }); }
    });
    buscar.addEventListener("input", function () { estado.q = buscar.value.trim(); aplicar(); });
    aplicar();
  }

  /* formulario B2B: validación en el navegador */
  var form = document.getElementById("form-b2b");
  if (form) {
    var error = document.getElementById("form-error");
    var exito = document.getElementById("form-exito");
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var faltan = [];
      form.querySelectorAll("[required]").forEach(function (c) {
        var falta = c.type === "checkbox" ? !c.checked : !c.value.trim();
        c.setAttribute("aria-invalid", falta ? "true" : "false");
        if (falta) faltan.push(c);
      });
      var correo = form.querySelector("[name=correo]");
      if (correo.value && !correo.checkValidity()) { correo.setAttribute("aria-invalid", "true"); faltan.push(correo); }
      if (faltan.length) {
        error.textContent = faltan[0].name === "autoriza" ? "Para enviar la solicitud necesitamos tu autorización de tratamiento de datos." : "Revisa los campos marcados en rojo.";
        faltan[0].focus();
        return;
      }
      error.textContent = "";
      exito.hidden = false;
      exito.focus();
    });
  }
})();
