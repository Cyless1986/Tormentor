"use strict";
(() => {
  if (window.tormentorNavigation || !window.AbortController) return;
  const persistent = document.createElement("div");
  persistent.id = "portal-persistent";
  const player = document.querySelector(".global-music");
  if (player) persistent.append(player);
  document.body.append(persistent);
  const api = window.tormentorNavigation = {scope:new AbortController()};
  let busy = false;
  let index = Number(history.state?.tormentor?.index) || 0;
  const scrollPositions = new Map();
  history.replaceState({...history.state, tormentor:{index}}, "", location.href);
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";

  function localPage(url) {
    return url.origin === location.origin && !/^\/(?:media|api)\//.test(url.pathname)
      && !/\/(?:file|portrait)(?:\/|$)/.test(url.pathname)
      && !/\.(?:pdf|zip|apk|mp4|mp3|wav|png|jpe?g|webp)$/i.test(url.pathname)
      && url.pathname !== "/reset-password";
  }
  function confirmLeaving() {
    return !document.querySelector("form[data-portal-dirty]")
      || window.confirm("Du hast ungespeicherte Änderungen. Trotzdem die Seite wechseln?");
  }
  async function loadScript(source) {
    const url = new URL(source, location.href);
    if (url.origin !== location.origin) throw new Error("Unexpected script origin");
    if (["/media/portal-music.js", "/media/portal-navigation.js"].includes(url.pathname)) return;
    url.searchParams.set("page", "1");
    const script = document.createElement("script");
    script.async = false;
    script.src = url.href;
    await new Promise((resolve,reject) => {
      script.onload = resolve;
      script.onerror = () => reject(new Error("Page script failed"));
      document.body.append(script);
    });
  }
  async function navigate(url, mode="push", targetIndex=null) {
    if (busy) return;
    if (!confirmLeaving()) {
      if (mode === "pop") history.go(index - targetIndex);
      return;
    }
    busy = true;
    const currentMain = document.querySelector("main");
    currentMain?.setAttribute("aria-busy", "true");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    let committed = false;
    try {
      const response = await fetch(url, {credentials:"same-origin", cache:"no-store", signal:controller.signal});
      const destination = new URL(response.url);
      if (!localPage(destination) || !response.headers.get("Content-Type")?.includes("text/html")) {
        location.assign(destination.href); return;
      }
      const parsed = new DOMParser().parseFromString(await response.text(), "text/html");
      if (!parsed.querySelector("header") || !parsed.querySelector("main")) throw new Error("Not a portal page");
      const scripts = [...parsed.querySelectorAll("script[src]")].map(script => script.getAttribute("src"));
      parsed.querySelectorAll("script, .global-music, #portal-persistent").forEach(node => node.remove());
      scrollPositions.set(index, [scrollX, scrollY]);
      api.scope.abort();
      api.scope = new AbortController();
      // Never detach the player: removing a media node can interrupt playback.
      document.head.replaceChildren(...parsed.head.childNodes);
      for (const node of [...document.body.childNodes]) if (node !== persistent) node.remove();
      document.body.append(...parsed.body.childNodes);
      committed = true;
      if (mode === "push") {
        index += 1;
        history.pushState({tormentor:{index}}, "", destination.href);
      } else {
        index = targetIndex;
        history.replaceState({...history.state,tormentor:{index}}, "", destination.href);
      }
      await Promise.all(scripts.map(source => loadScript(source)));
      const main = document.querySelector("main");
      main.tabIndex = -1;
      main.focus({preventScroll:true});
      const position = mode === "pop" ? scrollPositions.get(index) : null;
      if (position) scrollTo(...position);
      else if (destination.hash) document.getElementById(decodeURIComponent(destination.hash.slice(1)))?.scrollIntoView();
      else scrollTo(0,0);
      document.dispatchEvent(new Event("tormentor:navigated"));
    } catch (error) {
      if (committed) location.reload();
      else location.assign(url);
    } finally {
      clearTimeout(timeout);
      busy = false;
      document.querySelector("main")?.removeAttribute("aria-busy");
    }
  }
  document.addEventListener("click", event => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest("a[href]");
    if (!link || link.download || (link.target && link.target !== "_self") || link.closest("[data-full-navigation]")) return;
    const url = new URL(link.href);
    if (!localPage(url)) return;
    if (url.pathname === location.pathname && url.search === location.search && url.hash) return;
    event.preventDefault();
    navigate(url.href);
  });
  document.addEventListener("submit", event => {
    const form = event.target;
    if (event.defaultPrevented || !(form instanceof HTMLFormElement)) return;
    const method = (event.submitter?.getAttribute("formmethod") || form.method).toLowerCase();
    if (method !== "get" || (form.target && form.target !== "_self")) return;
    const url = new URL(event.submitter?.getAttribute("formaction") || form.action, location.href);
    if (!localPage(url)) return;
    url.search = new URLSearchParams(new FormData(form, event.submitter));
    event.preventDefault();
    navigate(url.href);
  });
  window.addEventListener("popstate", event => {
    const target = event.state?.tormentor?.index;
    if (!Number.isInteger(target)) { location.reload(); return; }
    if (target === index) return;
    navigate(location.href, "pop", target);
  });
})();
