/* Apuração por IA · menu único de navegação (Design: Mateus Paiva)
   Uso: <script src="{raiz}/menu.js" defer></script> em qualquer página do site. */
(function () {
  "use strict";
  if (document.querySelector(".apm")) return;
  var me = document.currentScript || document.querySelector('script[src$="menu.js"]');
  var root = me ? me.src.replace(/menu\.js(\?.*)?$/, "") : "/";
  var ITEMS = [
    { href: "", label: "Ao vivo 2026", sub: "2º turno presidencial, apuração em tempo real" },
    { href: "historico/", label: "Histórico", sub: "Todos os 2º turnos presidenciais, 1989–2026" },
    { href: "mapa/", label: "Mapa do voto", sub: "Presidente cidade por cidade, 2018, 2022 e 2026" },
    { href: "municipios/", label: "Prefeitos e vereadores", sub: "Todas as cidades, 2016, 2020 e 2024" },
    { href: "mundo/", label: "Mundo", sub: "Argentina, EUA e França comparados ao Brasil" },
    { href: "calendario/", label: "Calendário", sub: "Próximas eleições, com contagem regressiva" }
  ];
  var here = location.href.split(/[?#]/)[0].replace(/index\.html$/, "");
  var current = -1;
  ITEMS.forEach(function (it, i) {
    var full = root + it.href;
    if (here === full || (it.href && here.indexOf(full) === 0)) current = i;
  });

  var css =
    ".apm{position:sticky;top:0;z-index:50;background:rgba(8,13,24,.86);-webkit-backdrop-filter:saturate(1.4) blur(14px);backdrop-filter:saturate(1.4) blur(14px);border-bottom:1px solid rgba(255,255,255,.08);font-family:Manrope,system-ui,-apple-system,'Segoe UI',sans-serif}" +
    ".apm-in{max-width:1080px;margin:0 auto;height:56px;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:0 max(16px,env(safe-area-inset-right,0px)) 0 max(16px,env(safe-area-inset-left,0px))}" +
    ".apm-brand{display:flex;align-items:center;gap:9px;text-decoration:none;color:#EEF2F8;min-width:0}" +
    ".apm-dot{width:10px;height:10px;border-radius:50%;background:#E2B84B;box-shadow:0 0 0 4px rgba(226,184,75,.18);flex:none}" +
    ".apm-brand b{font:800 15.5px/1 Sora,system-ui,sans-serif;letter-spacing:-.01em;white-space:nowrap}" +
    ".apm-brand small{display:block;font:700 9.5px/1 Manrope,system-ui,sans-serif;letter-spacing:.18em;color:#E2B84B;margin-top:4px;white-space:nowrap}" +
    ".apm-links{display:flex;gap:4px;list-style:none;margin:0;padding:0}" +
    ".apm-links a{display:block;padding:8px 12px;border-radius:999px;font:700 13.5px/1 Manrope,system-ui,sans-serif;color:#C9D2E3;text-decoration:none;white-space:nowrap}" +
    ".apm-links a:hover{background:rgba(255,255,255,.06);color:#EEF2F8}" +
    ".apm-links a[aria-current]{background:rgba(226,184,75,.14);color:#E2B84B}" +
    ".apm-links a:focus-visible,.apm-btn:focus-visible,.apm-brand:focus-visible{outline:2px solid #E2B84B;outline-offset:2px}" +
    ".apm-btn{display:none;align-items:center;gap:8px;font:700 14px Manrope,system-ui,sans-serif;color:#EEF2F8;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);border-radius:999px;padding:9px 14px;cursor:pointer}" +
    ".apm-btn i{display:block;width:16px;height:2px;background:currentColor;border-radius:2px;position:relative}" +
    ".apm-btn i:before,.apm-btn i:after{content:'';position:absolute;left:0;width:16px;height:2px;background:currentColor;border-radius:2px;transition:transform .2s}" +
    ".apm-btn i:before{top:-5px}.apm-btn i:after{top:5px}" +
    ".apm-btn[aria-expanded=true] i{background:transparent}" +
    ".apm-btn[aria-expanded=true] i:before{transform:translateY(5px) rotate(45deg)}" +
    ".apm-btn[aria-expanded=true] i:after{transform:translateY(-5px) rotate(-45deg)}" +
    ".apm-drawer{display:none}" +
    "@media (max-width:1020px){.apm-links{display:none}.apm-btn{display:inline-flex}" +
    ".apm-drawer{position:absolute;left:0;right:0;top:56px;background:#0B1220;border-bottom:1px solid rgba(255,255,255,.1);box-shadow:0 24px 40px -12px rgba(0,0,0,.7);padding:10px max(16px,env(safe-area-inset-right,0px)) 18px max(16px,env(safe-area-inset-left,0px))}" +
    ".apm-drawer.open{display:block}" +
    ".apm-drawer a{display:block;padding:14px 14px;border-radius:14px;text-decoration:none;color:#EEF2F8;border:1px solid transparent}" +
    ".apm-drawer a+a{margin-top:4px}" +
    ".apm-drawer a b{display:block;font:700 17px/1.2 Sora,system-ui,sans-serif}" +
    ".apm-drawer a span{display:block;font:500 13px/1.4 Manrope,system-ui,sans-serif;color:#8C97AE;margin-top:3px}" +
    ".apm-drawer a[aria-current]{background:rgba(226,184,75,.1);border-color:rgba(226,184,75,.35)}" +
    ".apm-drawer a[aria-current] b{color:#E2B84B}" +
    ".apm-drawer .apm-sig{font:700 12px Manrope,system-ui,sans-serif;color:#8C97AE;letter-spacing:.06em;padding:12px 14px 0}" +
    ".apm-drawer .apm-sig b{color:#E2B84B}}" +
    "@media (prefers-reduced-motion:reduce){.apm-btn i:before,.apm-btn i:after{transition:none}}";

  var st = document.createElement("style");
  st.textContent = css;
  document.head.appendChild(st);

  var cur = function (i) { return i === current ? ' aria-current="page"' : ""; };
  var bar = document.createElement("header");
  bar.className = "apm";
  bar.innerHTML =
    '<div class="apm-in">' +
      '<a class="apm-brand" href="' + root + '"><span class="apm-dot" aria-hidden="true"></span><span><b>Apuração por IA</b><small>DESIGN · MATEUS PAIVA</small></span></a>' +
      '<nav aria-label="Menu principal"><ul class="apm-links">' +
        ITEMS.map(function (it, i) { return '<li><a href="' + root + it.href + '"' + cur(i) + ">" + it.label + "</a></li>"; }).join("") +
      "</ul></nav>" +
      '<button class="apm-btn" type="button" aria-expanded="false" aria-controls="apm-drawer"><i aria-hidden="true"></i>Menu</button>' +
    "</div>" +
    '<nav class="apm-drawer" id="apm-drawer" aria-label="Menu principal">' +
      ITEMS.map(function (it, i) { return '<a href="' + root + it.href + '"' + cur(i) + "><b>" + it.label + "</b><span>" + it.sub + "</span></a>"; }).join("") +
      '<div class="apm-sig">Dados oficiais · <b>Design Mateus Paiva</b></div>' +
    "</nav>";
  document.body.insertBefore(bar, document.body.firstChild);

  var btn = bar.querySelector(".apm-btn"), dr = bar.querySelector(".apm-drawer");
  function setOpen(o) { btn.setAttribute("aria-expanded", String(o)); dr.classList.toggle("open", o); }
  btn.addEventListener("click", function () { setOpen(btn.getAttribute("aria-expanded") !== "true"); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") setOpen(false); });
  document.addEventListener("click", function (e) { if (!bar.contains(e.target)) setOpen(false); });
})();
