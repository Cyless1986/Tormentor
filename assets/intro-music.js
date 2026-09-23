"use strict";
(() => {
  const audio = document.getElementById("intro-music");
  if (!audio) return;
  const read = key => { try { return localStorage.getItem(key); } catch { return null; } };
  const save = (key, value) => { try { localStorage.setItem(key, value); } catch {} };
  audio.volume = 0.3;
  let leaving = false;
  audio.addEventListener("play", () => save("tormentor.intro.enabled", "yes"));
  audio.addEventListener("pause", () => {
    if (!leaving) save("tormentor.intro.enabled", "no");
  });
  audio.addEventListener("loadedmetadata", () => {
    const position = Number(read("tormentor.intro.position"));
    if (Number.isFinite(position) && position > 0 && position < audio.duration) audio.currentTime = position;
  }, { once: true });
  window.addEventListener("pagehide", () => {
    leaving = true;
    save("tormentor.intro.position", String(audio.currentTime));
    audio.pause();
  });
  if (read("tormentor.intro.enabled") === "yes") audio.play().catch(() => {});
})();
