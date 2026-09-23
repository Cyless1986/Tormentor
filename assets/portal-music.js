"use strict";
(() => {
  const audio = document.getElementById("intro-music") || document.getElementById("dashboard-music");
  if (!audio) return;
  const status = document.getElementById("music-status");
  const key = "tormentor.music.rising-moon.";
  const read = name => { try { return localStorage.getItem(key + name); } catch { return null; } };
  const save = (name, value) => { try { localStorage.setItem(key + name, String(value)); } catch {} };
  const message = text => { if (status) status.textContent = text; };
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
    message("Rising Moon läuft in einer Schleife. Mit Pause ausschalten.");
  });
  audio.addEventListener("pause", () => {
    if (!leaving) save("enabled", "no");
    rememberPosition();
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
  window.addEventListener("pagehide", () => {
    leaving = true;
    rememberPosition();
    audio.pause();
  });
  window.addEventListener("pageshow", () => { leaving = false; });
  if (read("enabled") === "yes") audio.play().catch(() => {
    message("Mit Play Musik fortsetzen – dein Browser benötigt dafür einen Klick.");
  });
})();
