"use strict";
(() => {
  const audio = document.getElementById("global-music");
  if (!audio) return;
  const toggle = document.getElementById("music-toggle");
  const status = document.getElementById("music-status");
  const key = "tormentor.music.rising-moon.";
  const read = name => { try { return localStorage.getItem(key + name); } catch { return null; } };
  const save = (name, value) => { try { localStorage.setItem(key + name, String(value)); } catch {} };
  const message = text => { if (status) status.textContent = text; if (toggle) toggle.title = text; };
  const updateToggle = () => {
    if (!toggle) return;
    toggle.textContent = audio.paused ? "▶ Musik" : "Ⅱ Musik";
    toggle.setAttribute("aria-pressed", String(!audio.paused));
    toggle.setAttribute("aria-label", audio.paused ? "Titelmusik abspielen" : "Titelmusik pausieren");
  };
  if (toggle) toggle.addEventListener("click", () => {
    if (!audio.paused) audio.pause();
    else audio.play().catch(() => message("Mit einem weiteren Klick Musik starten. Bitte bei Bedarf die Audiofreigabe des Browsers prüfen."));
  });
  const volume = read("volume");
  audio.volume = volume !== null && Number.isFinite(Number(volume)) ? Math.min(1, Math.max(0, Number(volume))) : 0.2;
  audio.muted = read("muted") === "yes";
  let leaving = false;
  const rememberPosition = () => save("position", audio.currentTime);
  audio.addEventListener("loadedmetadata", () => {
    const position = Number(read("position"));
    if (Number.isFinite(position) && position > 0 && position < audio.duration) audio.currentTime = position;
  }, { once: true });
  audio.addEventListener("play", () => {
    save("enabled", "yes");
    updateToggle();
    message("Rising Moon läuft in einer Schleife. Mit Pause ausschalten.");
  });
  audio.addEventListener("pause", () => {
    if (!leaving) save("enabled", "no");
    rememberPosition();
    updateToggle();
    message("Musik pausiert. Mit Play wieder einschalten.");
  });
  audio.addEventListener("volumechange", () => {
    save("volume", audio.volume);
    save("muted", audio.muted ? "yes" : "no");
  });
  audio.addEventListener("error", () => message("Die Musik konnte nicht geladen werden. Bitte die Seite erneut laden."));
  document.addEventListener("click", event => {
    if (event.target.closest("[data-video]")) audio.pause();
  }, true);
  document.addEventListener("play", event => {
    if (event.target !== audio && !(event.target instanceof HTMLMediaElement && event.target.muted)) audio.pause();
  }, true);
  let lastSaved = 0;
  audio.addEventListener("timeupdate", () => {
    if (Date.now() - lastSaved > 1000) { rememberPosition(); lastSaved = Date.now(); }
  });
  window.addEventListener("pagehide", () => {
    leaving = true;
    rememberPosition();
    audio.pause();
  });
  window.addEventListener("pageshow", event => {
    leaving = false;
    if (event.persisted) {
      const position = Number(read("position"));
      if (Number.isFinite(position) && position >= 0 && position < audio.duration) audio.currentTime = position;
      if (read("enabled") === "yes") audio.play().catch(() => message("Mit Musik die Wiedergabe fortsetzen."));
    }
  });
  updateToggle();
  if (read("enabled") === "yes") audio.play().catch(() => {
    message("Mit Play Musik fortsetzen – dein Browser benötigt dafür einen Klick.");
  });
})();
