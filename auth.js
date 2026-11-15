/* Apuração por IA · login (Supabase). Design: Mateus Paiva
   Configuração: preencha URL e chave pública (anon) do seu projeto Supabase.
   A chave anon é pública por natureza; a proteção vem das regras (RLS) do banco. */
(function () {
  "use strict";
  var CONFIG = {
    url: "",       // ex.: https://abcdefgh.supabase.co
    anonKey: ""    // Project Settings > API > Project API keys > anon public
  };
  var me = document.currentScript || document.querySelector('script[src$="auth.js"]');
  var root = me ? me.src.replace(/auth\.js(\?.*)?$/, "") : "/";
  var ready = [], state = { client: null, user: null, perfil: null, configurado: !!(CONFIG.url && CONFIG.anonKey), carregado: false };

  function emit() { state.carregado = true; ready.splice(0).forEach(function (f) { try { f(state); } catch (e) {} }); listeners.forEach(function (f) { try { f(state); } catch (e) {} }); }
  var listeners = [];
  window.APIA = {
    root: root,
    estado: function () { return state; },
    pronto: function (f) { if (state.carregado) f(state); else ready.push(f); },
    aoMudar: function (f) { listeners.push(f); },
    entrarEmail: function (email, volta) {
      return state.client.auth.signInWithOtp({ email: email, options: { emailRedirectTo: volta || (root + "conta/") } });
    },
    entrarGoogle: function (volta) {
      return state.client.auth.signInWithOAuth({ provider: "google", options: { redirectTo: volta || (root + "conta/") } });
    },
    sair: function () { return state.client.auth.signOut().then(function () { location.href = root; }); },
    pode: function (cd) {
      var p = state.perfil; if (!p) return false;
      if (p.validade && new Date(p.validade + "T23:59:59") < new Date()) return false;
      return p.plano === "admin" || p.plano === "pro" || (p.plano === "raiox" && (p.cidades || []).indexOf(String(cd)) >= 0);
    }
  };

  function carregarPerfil() {
    if (!state.user) { state.perfil = null; return Promise.resolve(); }
    return state.client.from("perfis").select("*").eq("id", state.user.id).maybeSingle().then(function (r) { state.perfil = r.data || null; });
  }
  function menu() {
    var bar = document.querySelector(".apm-in");
    if (!bar || bar.querySelector(".apm-acc")) return;
    var a = document.createElement("a");
    a.className = "apm-acc";
    a.style.cssText = "margin-left:8px;font:700 13px Manrope,system-ui,sans-serif;color:#0B1220;background:#E2B84B;border-radius:999px;padding:8px 14px;text-decoration:none;white-space:nowrap";
    bar.appendChild(a);
    var upd = function () {
      if (state.user) { a.textContent = "Minha conta"; a.href = root + "conta/"; }
      else { a.textContent = "Entrar"; a.href = root + "entrar/?volta=" + encodeURIComponent(location.href); }
    };
    upd(); listeners.push(upd);
  }
  function start() {
    if (!state.configurado || !window.supabase) { emit(); return; }
    state.client = window.supabase.createClient(CONFIG.url, CONFIG.anonKey, { auth: { persistSession: true, detectSessionInUrl: true } });
    state.client.auth.getSession().then(function (r) {
      state.user = r.data.session ? r.data.session.user : null;
      return carregarPerfil();
    }).then(emit, emit);
    state.client.auth.onAuthStateChange(function (_ev, session) {
      var u = session ? session.user : null;
      if ((u && u.id) === (state.user && state.user.id)) return;
      state.user = u; carregarPerfil().then(emit, emit);
    });
  }
  function boot() {
    var tries = 0;
    (function waitMenu() { if (document.querySelector(".apm-in") || tries++ > 40) { if (state.configurado) menu(); } else setTimeout(waitMenu, 50); })();
    if (!state.configurado) { emit(); return; }
    var s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js";
    s.onload = start; s.onerror = function () { emit(); };
    document.head.appendChild(s);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
