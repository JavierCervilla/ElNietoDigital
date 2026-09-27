// Timeline de la presentación, COMPARTIDO por el horizontal (index.html) y el vertical (vertical/index.html).
// Lo que cambia entre formatos no está aquí: son las posiciones de estilos.css (+ los overrides del vertical) y
// los recorridos de window.NIETO_FORMATO, que declara cada index.html antes de cargar este fichero.
// Uso (en cada index.html, inline, para que el linter de HyperFrames vea el registro):
//   window.__timelines = window.__timelines || {};
//   window.__timelines["main"] = window.construirPresentacion(window.NIETO_FORMATO);
window.construirPresentacion = function (F) {
  var NAR = "#C8461F",
    AZU = "#1F2A44",
    CRE = "#FBF7F0";
  var T = window.NIETO_TIEMPOS,
    C = window.NIETO_CUES,
    FIN = T.duracion;
  var tl = gsap.timeline({ paused: true });

  function $(id) {
    return document.getElementById(id);
  }
  function el(tag, cls, parent, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    if (parent) parent.appendChild(e);
    return e;
  }
  // PRNG con semilla: nada de Math.random (el render busca fotograma a fotograma).
  function mulberry32(a) {
    return function () {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  var rnd = mulberry32(20);

  function sube(sel, t) {
    tl.fromTo(sel, { yPercent: 105, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 0.7, ease: "power4.out" }, t);
  }

  // Mano (la misma en S1, S6 y S9): tiembla con miedo, se detiene ante la duda y al final pulsa segura.
  var MANO =
    '<svg viewBox="0 0 200 300" style="width:230px;height:345px;display:block;overflow:visible">' +
    '<path d="M70 44 A20 20 0 0 1 110 44 L110 136 A15 15 0 0 1 140 134 A14 14 0 0 1 168 146 L170 236 Q170 300 112 312 L72 312 Q40 304 38 244 L36 206 Q8 190 16 164 Q26 142 50 160 L70 176 Z" fill="#FBF7F0" stroke="#1F2A44" stroke-width="8" stroke-linejoin="round"/>' +
    '<path d="M110 136 V176 M140 134 V180" stroke="#1F2A44" stroke-width="6" stroke-linecap="round" fill="none" opacity="0.55"/>' +
    "</svg>";
  ["hand1", "hand6", "hand9"].forEach(function (id) {
    $(id).innerHTML = MANO;
  });

  // ── Nota de voz: barras que respiran con la locución (envolvente pre-calculada, determinista) ──
  var bars = [];
  for (var b = 0; b < 24; b++) {
    var bar = el("div", "vb", $("vn-bars"));
    bar.style.left = b * 6 + "px";
    bars.push(bar);
  }
  var FORMA = bars.map(function (_, i) {
    return 0.5 + 0.5 * Math.pow(Math.sin(i * 1.7 + 0.6), 2);
  });
  function dibujaVoz(f) {
    for (var i = 0; i < bars.length; i++) {
      var k = f - Math.round(Math.abs(i - 11.5) * 0.55);
      var e = k >= 0 && k < T.env.length ? T.env[k] : 0;
      bars[i].style.transform = "scaleY(" + (0.14 + 0.86 * e * FORMA[i]).toFixed(3) + ")";
    }
  }
  for (var f = 0; f < Math.round(FIN * T.fps); f++) {
    tl.call(dibujaVoz, [f], f / T.fps);
  }

  // ── Subtítulos: por frases (corte en la puntuación), ≤ 52 caracteres; si una frase no cabe, se parte
  //    antes de una conjunción. Solo se juntan frases tras una coma. Subrayado palabra a palabra. ──
  var MAX = F.maxSubtitulo;
  function largo(ws) {
    return ws.reduce(function (a, p) {
      return a + p.p.length + 1;
    }, -1);
  }
  // Corte de mínima irregularidad (como un maquetador): trozos ≤ MAX lo más parejos posible; cortar antes de una
  // conjunción es más barato y dejar un trozo colgando de un artículo o preposición («…partido a la») es más caro.
  // El corte voraz dejaba huérfanos con MAX 44 («…trámites desde» / «casa.»).
  function partir(f) {
    var n = f.length,
      mejor = [0],
      desde = [0];
    for (var j = 1; j <= n; j++) {
      mejor[j] = Infinity;
      for (var i = j - 1; i >= 0; i--) {
        var l = largo(f.slice(i, j));
        if (l > MAX && i < j - 1) break;
        var coste = mejor[i] + Math.pow(Math.max(0, MAX - l), 2);
        if (i > 0 && /^(y|e|o|que|con|para)$/i.test(f[i].p)) coste -= 200;
        if (j < n && /^(a|de|la|el|las|los|una|un|en|y|con|sus|que)$/i.test(f[j - 1].p)) coste += 300;
        if (coste < mejor[j]) {
          mejor[j] = coste;
          desde[j] = i;
        }
      }
    }
    var out = [];
    for (var k = n; k > 0; k = desde[k]) out.unshift(f.slice(desde[k], k));
    return out;
  }
  var trozos = [];
  T.lineas.forEach(function (l) {
    var frases = [],
      cur = [];
    l.palabras.forEach(function (p) {
      cur.push(p);
      if (/[,.:;…?!]$/.test(p.p)) {
        frases.push(cur);
        cur = [];
      }
    });
    if (cur.length) frases.push(cur);
    var piezas = [];
    frases.forEach(function (f) {
      piezas = piezas.concat(largo(f) > MAX ? partir(f) : [f]);
    });
    var juntas = [];
    piezas.forEach(function (p) {
      var u = juntas[juntas.length - 1];
      if (u && /,$/.test(u[u.length - 1].p) && largo(u) + 1 + largo(p) <= MAX) juntas[juntas.length - 1] = u.concat(p);
      else juntas.push(p);
    });
    juntas.forEach(function (ws) {
      trozos.push({ palabras: ws, linea: l });
    });
  });
  trozos.forEach(function (tr, k) {
    var c = el("div", "chunk", $("caps"));
    var inner = el("div", "chunk-in", c);
    tr.palabras.forEach(function (p, j) {
      var w = el("span", "w", inner, p.p + "<i></i>");
      if (j < tr.palabras.length - 1) inner.appendChild(document.createTextNode(" "));
      p._u = w.querySelector("i");
    });
    var sig = trozos[k + 1];
    var desde = tr.palabras[0].t0 - 0.12;
    var hasta = sig && sig.linea === tr.linea ? sig.palabras[0].t0 - 0.21 : tr.linea.t1 + 0.45;
    if (sig) hasta = Math.min(hasta, sig.palabras[0].t0 - 0.21);
    tl.fromTo(c, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.16, ease: "power2.out" }, desde);
    tl.to(c, { opacity: 0, duration: 0.08, ease: "none" }, hasta);
    tr.palabras.forEach(function (p, j) {
      tl.fromTo(p._u, { scaleX: 0, opacity: 1 }, { scaleX: 1, duration: 0.14, ease: "power2.out" }, p.t0);
      var n = tr.palabras[j + 1];
      if (n) tl.to(p._u, { opacity: 0, duration: 0.1 }, n.t0);
    });
  });

  // Papel de fondo: deriva lenta durante todo el vídeo.
  tl.fromTo("#paper", { x: 0, y: 0 }, { x: -20, y: -80, duration: FIN, ease: "none" }, 0);

  // ═══ S1 · el ruido ═══════════════════════════════════════════════════════════
  // Cámara que se acerca mientras crece la tensión.
  tl.fromTo("#w1", { scale: 1 }, { scale: 1.07, duration: C.congela, ease: "power1.in" }, 0);
  tl.from("#hero", { y: 60, opacity: 0, duration: 0.7, ease: "power3.out" }, 0.1);
  // «¿Le suena?»: vibra.
  [0, 1, 2, 3, 4, 5, 6, 7].forEach(function (k) {
    tl.to("#hero", { x: k % 2 ? -9 : 9, duration: 0.045, ease: "none" }, C.vibra + k * 0.045);
  });
  tl.to("#hero", { x: 0, duration: 0.05 }, C.vibra + 0.36);
  // Mensaje incomprensible.
  tl.to("#bubble", { scale: 1, duration: 0.5, ease: "back.out(1.7)" }, C.mensaje);
  // Notificaciones en la pantalla y contador.
  for (var n = 0; n < 7; n++) {
    var nt = el("div", "noti", $("notis"));
    nt.style.top = n * 54 + "px";
  }
  var bnum = [];
  for (var q = 1; q <= C.jerga.length + 1; q++) {
    var s = el("div", "bn", $("badge"), q > 9 ? "9+" : String(q));
    bnum.push(s);
  }
  tl.to("#badge", { scale: 1, duration: 0.35, ease: "back.out(2.4)" }, C.mensaje + 0.1);
  tl.set(bnum[0], { opacity: 1 }, C.mensaje + 0.1);
  tl.to(".noti:nth-child(1)", { opacity: 1, duration: 0.2 }, C.mensaje + 0.1);
  // La jerga se amontona, cada vez más deprisa.
  var JERGA = [
    ["Código OTP", "n", -6],
    ["Cookies", "o", 4],
    ["Bizum", "r", 5],
    ["Actualización pendiente", "o", -3],
    ["ChatGPT", "n", -5],
    ["Cl@ve PIN", "r", 5],
    ["Token", "o", 6],
    ["Aceptar términos", "n", -4],
    ["Nube", "r", -3],
    ["2FA", "n", -6],
    ["Bluetooth", "o", 3],
    ["Enlace", "r", 4],
    ["Wifi", "o", -4],
    ["Spam", "n", 5],
    ["Descargar", "r", -3],
    ["Contraseña", "o", 4],
  ];
  C.jerga.forEach(function (t, k) {
    var d = JERGA[k % JERGA.length],
      pos = F.jerga[k % F.jerga.length];
    var p = el("div", "pill " + d[1], $("pills"), d[0]);
    p.style.left = pos[0] + "px";
    p.style.top = pos[1] + "px";
    tl.fromTo(p, { scale: 0, rotation: d[2] * 3 }, { scale: 1, rotation: d[2], duration: 0.34, ease: "back.out(2)" }, t);
    // Deriva nerviosa mientras dure el ruido.
    tl.to(p, { x: (rnd() - 0.5) * 40, y: (rnd() - 0.5) * 30, duration: C.congela - t, ease: "sine.inOut" }, t + 0.3);
    tl.set(bnum[k], { opacity: 0 }, t);
    tl.set(bnum[k + 1], { opacity: 1 }, t);
    if (k < 6) tl.to(".noti:nth-child(" + (k + 2) + ")", { opacity: 1, duration: 0.15 }, t);
  });
  // «…y ese miedo a tocar algo»: la mano entra temblando y se queda a un dedo de la pantalla.
  tl.fromTo("#hand1", { y: 0 }, { y: F.mano1[0], duration: 0.8, ease: "power3.out" }, C.dedo - 0.3);
  for (var k2 = 0; k2 < 14; k2++) {
    tl.to("#hand1", { x: k2 % 2 ? -6 : 6, rotation: k2 % 2 ? -2 : 2, duration: 0.06, ease: "none" }, C.dedo + 0.5 + k2 * 0.06);
  }
  tl.to("#hand1", { y: F.mano1[1], duration: 0.3, ease: "power2.out" }, C.dedo + 0.5);
  // Congelado: se corta la música y todo se para un instante (el silencio antes de respirar).

  // ═══ S2 · «Respire.» ═════════════════════════════════════════════════════════
  var R = C.respire;
  tl.to("#w1", { scale: 1, duration: 1.6, ease: "power2.out" }, R);
  // Orden de salida barajado con semilla propia: `from: "random"` de GSAP usa Math.random y cada render salía
  // distinto (medido: dos renders del mismo fotograma no coincidían).
  var azar = mulberry32(8),
    orden = C.jerga.map(function (_, i) {
      return [azar(), i];
    });
  orden.sort(function (a, b) {
    return a[0] - b[0];
  });
  var turno = [];
  orden.forEach(function (o, k) {
    turno[o[1]] = k;
  });
  tl.to("#pills .pill", {
    scale: 0,
    opacity: 0,
    duration: 0.8,
    ease: "power2.in",
    stagger: function (i) {
      return turno[i] * 0.03;
    },
  }, R);
  tl.to("#bubble", { scale: 0, opacity: 0, duration: 0.5, ease: "power2.in" }, R);
  tl.to("#hand1", { y: 0, x: 0, rotation: 0, duration: 0.9, ease: "power2.in" }, R);
  tl.to("#badge", { scale: 0, duration: 0.35, ease: "back.in(2)" }, R + 0.1);
  tl.to(".noti", { opacity: 0, duration: 0.4, stagger: 0.05 }, R + 0.1);
  tl.fromTo("#ring", { scale: 0.6, opacity: 0.9 }, { scale: 2.6, opacity: 0, duration: 2.2, ease: "power2.out", immediateRender: false }, R);
  tl.to("#h-body", { attr: { fill: NAR }, duration: 1.2, ease: "power2.inOut" }, R + 0.2);
  tl.to(["#h-eyeL", "#h-eyeR"], { attr: { opacity: 1 }, duration: 0.3 }, R + 0.9);
  tl.fromTo(["#h-eyeL", "#h-eyeR"], { scale: 0, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.4, ease: "back.out(3)" }, R + 0.9);
  tl.to("#h-mouth", { attr: { opacity: 1 }, duration: 0.2 }, C.sonrisa - 0.2);
  tl.to("#hero", { x: F.heroCalma.x, y: F.heroCalma.y, duration: 1.0, ease: "power3.inOut" }, C.sonrisa - 0.35);
  tl.to("#h-mouth", { attr: { d: "M49 62 Q60 76 71 62" }, duration: 0.6, ease: "back.out(2)" }, C.sonrisa);
  sube("#s2-l1", C.sonrisa);
  sube("#s2-l2", C.muerde - 0.2);
  tl.to("#s2-under-p", { attr: { "stroke-dashoffset": 0 }, duration: 0.5, ease: "power2.inOut" }, C.muerde + 0.3);
  tl.to(["#h-eyeL", "#h-eyeR"], { scaleY: 0.1, duration: 0.07, yoyo: true, repeat: 1 }, C.muerde + 0.7);

  // ═══ S3 · qué es: el móvil se convierte en el logotipo ═══════════════════════
  var S3 = C.escena3;
  tl.to(["#s2-l1", "#s2-l2"], { yPercent: -105, duration: 0.5, ease: "power3.in", stagger: 0.06 }, S3 - 0.35);
  tl.to("#s2-under", { opacity: 0, duration: 0.3 }, S3 - 0.3);
  // El héroe (el móvil) viaja hasta el símbolo del logotipo y se funde con él (F.heroLogo lo calcula).
  tl.to("#hero", { x: F.heroLogo.x, y: F.heroLogo.y, scale: F.heroLogo.scale, transformOrigin: "0 0", duration: 0.9, ease: "power3.inOut" }, S3 - 0.2);
  tl.set("#s3", { opacity: 1 }, S3);
  tl.set("#logoLayer", { opacity: 1 }, S3 + 0.7);
  tl.set("#s1", { opacity: 0 }, S3 + 0.72);
  tl.from("#s3-eb", { y: 30, opacity: 0, duration: 0.5, ease: "power3.out" }, S3);
  tl.fromTo("#lk-w1", { y: 58 }, { y: 0, duration: 0.7, ease: "power4.out" }, C.logo - 0.25);
  tl.fromTo("#lk-w2", { y: 70 }, { y: 0, duration: 0.7, ease: "power4.out" }, C.logo + 0.05);
  // «la inteligencia artificial y el móvil»: el logo sube y aparecen las dos piezas.
  tl.to("#logo", { y: F.logoArriba.y, scale: F.logoArriba.scale, duration: 0.8, ease: "power3.inOut" }, C.ia - 0.45);
  tl.to("#s3-eb", { opacity: 0, duration: 0.3 }, C.ia - 0.45);
  tl.to("#chipIA", { scale: 1, duration: 0.5, ease: "back.out(1.8)" }, C.ia);
  tl.fromTo("#spk", { scale: 0.4, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.9, ease: "elastic.out(1, 0.5)" }, C.ia + 0.1);
  tl.to("#chipMas", { scale: 1, duration: 0.35, ease: "back.out(2)" }, C.movil - 0.25);
  tl.to("#chipMov", { scale: 1, duration: 0.5, ease: "back.out(1.8)" }, C.movil);
  // «…explicados con calma y sin palabras raras»: la jerga se tacha y se traduce.
  var X = C.traduce;
  tl.to(["#chipIA", "#chipMov", "#chipMas"], { y: -40, opacity: 0, duration: 0.4, ease: "power2.in", stagger: 0.05 }, X - 1.45);
  tl.fromTo("#jerga", { opacity: 0, x: -60 }, { opacity: 1, x: 0, duration: 0.6, ease: "power3.out" }, X - 1.0);
  tl.to(".strike-p", { attr: { "stroke-dashoffset": 0 }, duration: 0.3, ease: "power2.inOut", stagger: 0.22 }, X);
  tl.to("#jerga", { opacity: 0.45, duration: 0.4 }, X + 0.3);
  tl.to("#arrow-p", { attr: { "stroke-dashoffset": 0 }, duration: 0.5, ease: "power2.inOut" }, X + 0.15);
  tl.fromTo("#llana", { opacity: 0, x: 60, scale: 0.94 }, { opacity: 1, x: 0, scale: 1, duration: 0.6, ease: "back.out(1.6)" }, X + 0.35);
  tl.to("#w3", { scale: 1.03, duration: 7, ease: "none", transformOrigin: "50% 50%" }, S3);

  // ═══ Transición S3 → S4: barrido de bandas ═══════════════════════════════════
  var S4 = C.escena4;
  tl.to("#band-o", { x: 0, duration: 0.5, ease: "power3.in" }, S4 - 0.6);
  tl.to("#band-n", { x: 0, duration: 0.5, ease: "power3.in" }, S4 - 0.5);
  tl.set(["#s3", "#logoLayer"], { opacity: 0 }, S4 - 0.02);
  tl.set("#s4", { opacity: 1 }, S4 - 0.02);
  tl.to("#band-o", { x: 2900, duration: 0.6, ease: "power3.out" }, S4);
  tl.to("#band-n", { x: 2900, duration: 0.6, ease: "power3.out" }, S4 - 0.05);

  // ═══ S4 · de qué va: tres ideas, tres tarjetas ═══════════════════════════════
  tl.from("#s4-eb", { y: 30, opacity: 0, duration: 0.5, ease: "power3.out" }, S4 + 0.1);
  ["#c1", "#c2", "#c3"].forEach(function (id, k) {
    var t = C.tarjetas[k] - 0.08;
    tl.fromTo(id, { opacity: 0, y: 90, rotation: k === 1 ? 3 : -3, scale: 0.9 }, { opacity: 1, y: 0, rotation: 0, scale: 1, duration: 0.65, ease: "back.out(1.5)" }, t);
    if (k > 0) tl.to(["#c1", "#c2", "#c3"].slice(0, k), { y: 14, duration: 0.4, ease: "power2.out" }, t);
    tl.to(id, { y: -14, duration: 0.4, ease: "power2.out" }, t + 0.65);
  });
  tl.to("#c1-chk", { attr: { "stroke-dashoffset": 0 }, duration: 0.45, ease: "power2.out" }, C.tarjetas[0] + 0.4);
  [0, 1, 2].forEach(function (k) {
    tl.fromTo("#c2-d" + (k + 1), { y: 0 }, { y: -9, duration: 0.22, ease: "sine.inOut", yoyo: true, repeat: 5 }, C.tarjetas[1] + 0.35 + k * 0.12);
  });
  tl.fromTo("#c2-spk", { scale: 0, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.7, ease: "elastic.out(1, 0.45)" }, C.tarjetas[1] + 0.5);
  tl.from("#c3-doc", { y: 30, opacity: 0, duration: 0.45, ease: "back.out(2)" }, C.tarjetas[2] + 0.35);
  tl.to("#c3-chk", { attr: { "stroke-dashoffset": 0 }, duration: 0.35, ease: "power2.out" }, C.tarjetas[2] + 0.75);

  // ═══ Transición S4 → S5: las tres tarjetas se funden en UN vídeo ════════════
  var S5 = C.escena5;
  tl.to("#c1", Object.assign({ scale: 0.6, opacity: 0, duration: 0.55, ease: "power3.in" }, F.colapso.c1), S5 - 0.45);
  tl.to("#c3", Object.assign({ scale: 0.6, opacity: 0, duration: 0.55, ease: "power3.in" }, F.colapso.c3), S5 - 0.45);
  tl.to("#c2", { scale: 0.6, opacity: 0, duration: 0.55, ease: "power3.in" }, S5 - 0.4);
  tl.to("#s4-eb", { opacity: 0, duration: 0.3 }, S5 - 0.45);
  tl.set("#s5", { opacity: 1 }, S5 - 0.12);
  tl.set("#s4", { opacity: 0 }, S5 + 0.1);

  // ═══ S5 · una cosa nueva, paso a paso ════════════════════════════════════════
  tl.fromTo("#player", { scale: 0.3, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.7, ease: "back.out(1.3)" }, S5 - 0.1);
  tl.from(["#pl-eb", "#pl-title"], { y: 30, opacity: 0, duration: 0.5, ease: "power3.out", stagger: 0.08 }, S5 + 0.3);
  tl.to("#pl-fill", { scaleX: 1, duration: C.escena6 - S5, ease: "none" }, S5 + 0.3);
  tl.to("#uno", { scale: 1, duration: 0.5, ease: "back.out(2.6)" }, C.una);
  tl.to("#uno", { scale: 0.92, duration: 0.15, yoyo: true, repeat: 1 }, C.una + 0.5);
  ["#st1", "#st2", "#st3"].forEach(function (id, k) {
    tl.fromTo(id, { opacity: 0, x: -50 }, { opacity: 1, x: 0, duration: 0.45, ease: "power3.out" }, C.pasos[0] + k * 0.26);
  });
  tl.fromTo("#tphone", { opacity: 0, y: 80 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, C.pasos[1] - 0.3);
  tl.to("#st3 .num", { backgroundColor: NAR, duration: 0.3 }, C.pasos[2] - 0.3);
  tl.fromTo("#touch5", { scale: 1.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.45, ease: "power3.out" }, C.pasos[2]);
  tl.to("#touch5", { scale: 1.12, duration: 0.3, yoyo: true, repeat: 1, ease: "sine.inOut" }, C.pasos[2] + 0.45);
  tl.to("#chip5", { scale: 1, duration: 0.45, ease: "back.out(2)" }, C.pasos[2] + 0.2);
  tl.to("#touch5", { scale: 0.82, duration: 0.1, ease: "power2.in" }, C.toque - 0.1);
  tl.fromTo("#ripple5", { scale: 0.6, opacity: 0.6 }, { scale: 3.2, opacity: 0, duration: 0.7, ease: "power2.out", immediateRender: false }, C.toque);
  tl.to("#sl-fill", { scaleX: 0.92, duration: 0.7, ease: "power3.inOut" }, C.toque + 0.05);
  tl.to("#sl-knob", { x: 150, duration: 0.7, ease: "power3.inOut" }, C.toque + 0.05);
  tl.to("#touch5", { x: 150, duration: 0.7, ease: "power3.inOut" }, C.toque + 0.05);
  tl.to("#aa", { scale: 1.7, duration: 0.7, ease: "back.out(2)" }, C.toque + 0.2);

  // ═══ Transición S5 → S6: la cámara entra en el móvil ═════════════════════════
  var S6 = C.escena6;
  tl.to("#w5", { scale: 3.2, x: F.empuje.x, y: F.empuje.y, duration: 0.7, ease: "power3.in", transformOrigin: F.empuje.origen }, S6 - 0.55);
  tl.fromTo("#s6", { opacity: 0 }, { opacity: 1, duration: 0.3, ease: "none" }, S6 - 0.25);
  tl.set("#s5", { opacity: 0 }, S6 + 0.1);

  // ═══ S6 · alerta estafa ══════════════════════════════════════════════════════
  tl.fromTo("#sphone", { y: F.sphoneDesde }, { y: 0, duration: 0.7, ease: "power3.out" }, S6 - 0.2);
  tl.to("#sbub", { scale: 1, duration: 0.55, ease: "back.out(1.7)" }, C.estafa_llega);
  tl.to("#slink", { scale: 1, duration: 0.45, ease: "back.out(2)" }, C.estafa_llega + 0.35);
  tl.fromTo("#alerta", { opacity: 0, scale: 1.6, x: 0 }, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2.2)", transformOrigin: F.alertaOrigen }, C.alerta - 0.05);
  tl.fromTo("#stamp", { scale: 2.6, opacity: 0 }, { scale: 1, opacity: 1, rotation: -9, duration: 0.28, ease: "power4.in" }, C.sello - 0.28);
  [0, 1, 2, 3, 4, 5].forEach(function (k) {
    tl.to("#sphone", { x: k % 2 ? -12 : 12, duration: 0.04, ease: "none" }, C.sello + k * 0.04);
  });
  tl.to("#sphone", { x: 0, duration: 0.05 }, C.sello + 0.24);
  tl.to("#w6", { scale: 1.02, duration: 0.12, yoyo: true, repeat: 1, transformOrigin: "50% 50%" }, C.sello);
  // «Y recuerde: ante la duda, no toque nada.» La mano se acerca al botón… y se detiene.
  sube("#s6-l1", C.duda - 0.15);
  tl.fromTo("#hand6", { x: 0, y: 0 }, Object.assign({ duration: 0.9, ease: "power3.out" }, F.mano6.acerca), C.duda - 0.6);
  sube("#s6-l2", C.no_toque - 0.15);
  tl.to("#s6-mk", { scaleX: 1, duration: 0.5, ease: "power3.inOut" }, C.no_toque + 0.35);
  tl.to("#hand6", Object.assign({ duration: 0.6, ease: "power3.out" }, F.mano6.para), C.no_toque + 0.05);
  tl.to("#hand6", { x: 0, y: 0, duration: 0.8, ease: "power2.in" }, C.no_toque + 0.9);

  // ═══ Transición S6 → S7: iris desde el sello ═════════════════════════════════
  var S7 = C.escena7;
  tl.to("#s7", { clipPath: "circle(2300px at " + F.iris + ")", duration: 0.9, ease: "power3.in" }, S7 - 0.7);
  tl.set("#s6", { opacity: 0 }, S7 + 0.25);

  // ═══ S7 · quien aprende, enseña a otro ═══════════════════════════════════════
  var PERSONA =
    '<svg viewBox="0 0 170 170"><circle cx="85" cy="85" r="80" fill="#FBF7F0" stroke="#1F2A44" stroke-width="8"/>' +
    '<circle class="pc" cx="85" cy="66" r="26" fill="#1F2A44"/><path class="pc" d="M38 136 C44 104 62 96 85 96 C108 96 126 104 132 136 Z" fill="#1F2A44"/>' +
    '<circle class="ring" cx="85" cy="85" r="80" fill="#C8461F" opacity="0"/>' +
    '<circle class="pc2" cx="85" cy="66" r="26" fill="#FBF7F0" opacity="0"/><path class="pc2" d="M38 136 C44 104 62 96 85 96 C108 96 126 104 132 136 Z" fill="#FBF7F0" opacity="0"/></svg>';
  // [x, y, escala final, de quién aprende] — del formato
  var NODOS = F.nodos;
  var avs = NODOS.map(function (nd, i) {
    var a = el("div", "av", $("avs"), PERSONA);
    a.style.left = nd[0] - 85 + "px";
    a.style.top = nd[1] - 85 + "px";
    return a;
  });
  var arcos = NODOS.map(function (nd, i) {
    if (nd[3] < 0) return null;
    var o = NODOS[nd[3]];
    var mx = (o[0] + nd[0]) / 2,
      my = (o[1] + nd[1]) / 2 - 90;
    var p = document.createElementNS("http://www.w3.org/2000/svg", "path");
    p.setAttribute("d", "M" + o[0] + " " + o[1] + " Q" + mx + " " + my + " " + nd[0] + " " + nd[1]);
    p.setAttribute("pathLength", "1");
    p.setAttribute("stroke", i < 2 ? NAR : AZU);
    p.setAttribute("stroke-width", i < 2 ? "10" : "6");
    p.setAttribute("stroke-linecap", "round");
    p.setAttribute("fill", "none");
    p.setAttribute("stroke-dasharray", "1");
    p.setAttribute("stroke-dashoffset", "1");
    if (i >= 2) p.setAttribute("opacity", "0.55");
    $("net7").appendChild(p);
    return p;
  });
  function enciende(i, t) {
    tl.to(avs[i].querySelector(".ring"), { attr: { opacity: 1 }, duration: 0.3 }, t);
    tl.to(avs[i].querySelectorAll(".pc2"), { attr: { opacity: 1 }, duration: 0.3 }, t);
    tl.to(avs[i], { scale: "+=0.12", duration: 0.18, yoyo: true, repeat: 1, ease: "power2.out" }, t);
  }
  // Los dos primeros, grandes; luego la cámara se abre y la red crece.
  tl.fromTo(avs[0], { scale: 0 }, { scale: 1, duration: 0.5, ease: "back.out(2)" }, S7);
  tl.fromTo(avs[1], { scale: 0 }, { scale: 1, duration: 0.5, ease: "back.out(2)" }, S7 + 0.15);
  tl.set(avs[0], { x: -80 }, 0);
  tl.set(avs[1], { x: 80 }, 0);
  enciende(0, C.aprende);
  tl.set("#spark", { left: NODOS[0][0] - 125 + "px", top: NODOS[0][1] - 175 + "px" }, 0);
  tl.fromTo("#spark", { scale: 0 }, { scale: 1, duration: 0.6, ease: "elastic.out(1, 0.45)" }, C.aprende);
  tl.to("#spark", { scale: 0, duration: 0.3 }, C.otro + 0.4);
  tl.to(arcos[1], { attr: { "stroke-dashoffset": 0 }, duration: 0.55, ease: "power2.inOut" }, C.ensena);
  enciende(1, C.otro);
  tl.to(avs[0], { x: 0, scale: NODOS[0][2], duration: 0.8, ease: "power3.inOut" }, C.otro + 0.1);
  tl.to(avs[1], { x: 0, scale: NODOS[1][2], duration: 0.8, ease: "power3.inOut" }, C.otro + 0.1);
  C.red.forEach(function (t, k) {
    var i = k + 2;
    if (i >= NODOS.length) return;
    tl.to(arcos[i], { attr: { "stroke-dashoffset": 0 }, duration: 0.4, ease: "power2.out" }, t - 0.2);
    tl.fromTo(avs[i], { scale: 0 }, { scale: NODOS[i][2], duration: 0.4, ease: "back.out(2.2)" }, t - 0.05);
    enciende(i, t + 0.2);
  });
  sube("#s7-l1", C.nadie - 0.1);
  tl.to("#w7", { scale: 1.04, duration: 5.5, ease: "none", transformOrigin: "50% 60%" }, S7);

  // ═══ S8 · la voz es IA, y se dice ════════════════════════════════════════════
  var S8 = C.escena8;
  tl.set("#s8", { opacity: 1 }, S8);
  tl.to(avs, { scale: 0, duration: 0.4, ease: "back.in(2)", stagger: { each: 0.03, from: "end" } }, S8 - 0.35);
  tl.to("#net7 path", { opacity: 0, duration: 0.4 }, S8 - 0.3);
  tl.to("#s7-l1", { yPercent: -105, duration: 0.5, ease: "power3.in" }, S8 - 0.3);
  tl.set("#s7", { opacity: 0 }, S8 + 0.3);
  // La etiqueta que estuvo ahí todo el rato viaja al centro y se hace protagonista.
  tl.to("#vnote", { x: F.vnoteCentro.x, y: F.vnoteCentro.y, scale: F.vnoteCentro.scale, duration: 1.1, ease: "power3.inOut" }, S8 + 0.05);
  sube("#s8-l1", C.esta_voz - 0.1);
  sube("#s8-l2", C.ia_voz - 0.25);
  tl.to(["#s8-l1", "#s8-l2"], { yPercent: -105, opacity: 0, duration: 0.45, ease: "power3.in", stagger: 0.05 }, C.siempre - 0.95);
  sube("#s8-l3", C.siempre - 0.55);
  tl.fromTo("#vn-ok", { opacity: 0, scale: 0 }, { opacity: 1, scale: 1, duration: 0.45, ease: "back.out(2.6)" }, C.siempre - 0.2);
  tl.to("#vnote", { x: 0, y: 0, scale: 1, duration: 1.0, ease: "power3.inOut" }, C.siempre + 0.45);

  // ═══ S9 · «Suscríbase.» y cierre ═════════════════════════════════════════════
  var S9 = C.escena9;
  tl.set("#s9", { opacity: 1 }, S9 - 0.2);
  tl.to("#s8-l3", { yPercent: -105, duration: 0.45, ease: "power3.in" }, S9 - 0.5);
  tl.fromTo("#subBtn", { scale: 0 }, { scale: 1, duration: 0.55, ease: "back.out(1.8)" }, S9 - 0.1);
  tl.fromTo("#hand9", { y: 0 }, { y: F.mano9[0], duration: 0.6, ease: "power3.out" }, S9 + 0.05);
  tl.to("#hand9", { y: F.mano9[1], duration: 0.12, ease: "power2.in" }, C.suscribase_toque - 0.12);
  tl.to("#subBtn", { scale: 0.95, duration: 0.1, yoyo: true, repeat: 1 }, C.suscribase_toque);
  tl.fromTo("#ripple9", { scale: 0.4, opacity: 0.7 }, { scale: 4, opacity: 0, duration: 0.7, ease: "power2.out", immediateRender: false }, C.suscribase_toque);
  tl.set("#sb2", { opacity: 1 }, C.suscribase_toque + 0.06);
  tl.set("#sb1", { opacity: 0 }, C.suscribase_toque + 0.06);
  tl.to("#hand9", { y: 0, duration: 0.45, ease: "power2.in" }, C.suscribase_toque + 0.2);
  [0, 1, 2, 3].forEach(function (k) {
    tl.to("#bell", { rotation: k % 2 ? -14 : 14, svgOrigin: "46 14", duration: 0.07 }, C.suscribase_toque - 0.35 + k * 0.07);
  });
  tl.to("#bell", { rotation: 0, svgOrigin: "46 14", duration: 0.08 }, C.suscribase_toque - 0.07);
  // Logotipo final.
  var LF = C.logo_final;
  // El botón y la mano salen ANTES de que asome el logotipo: nada se pisa.
  tl.to("#subBtn", { scale: 0, opacity: 0, duration: 0.35, ease: "back.in(1.8)" }, LF - 0.5);
  tl.set("#logo", { y: F.logoFinal.y, scale: F.logoFinal.scale }, LF - 0.16);
  tl.set(["#lk-w1"], { y: 58 }, LF - 0.16);
  tl.set(["#lk-w2"], { y: 70 }, LF - 0.16);
  tl.set("#lk-m", { scale: 0, transformOrigin: "70px 70px" }, LF - 0.16);
  tl.set("#logoLayer", { opacity: 1 }, LF - 0.15);
  tl.fromTo("#lk-m", { scale: 0, transformOrigin: "70px 70px" }, { scale: 1, duration: 0.6, ease: "back.out(1.9)", immediateRender: false }, LF - 0.12);
  tl.to("#lk-w1", { y: 0, duration: 0.7, ease: "power4.out" }, LF + 0.15);
  tl.to("#lk-w2", { y: 0, duration: 0.7, ease: "power4.out" }, LF + 0.4);
  tl.fromTo("#tag", { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, LF + 0.8);
  tl.fromTo("#plat", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, T.lineas[8].t1 + 0.55);
  tl.to(["#lk-eyeL", "#lk-eyeR"], { scaleY: 0.1, transformOrigin: "50% 50%", duration: 0.07, yoyo: true, repeat: 1 }, C.guino - 1.4);
  tl.to("#lk-eyeR", { scaleY: 0.1, transformOrigin: "50% 50%", duration: 0.1, yoyo: true, repeat: 1, repeatDelay: 0.35 }, C.guino);
  tl.to("#logo", { scale: 0.93, duration: FIN - LF, ease: "none" }, LF + 0.4);
  return tl;
};
