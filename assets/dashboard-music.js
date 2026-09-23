"use strict";
(() => {
  const audio = document.getElementById("dashboard-music");
  const status = document.getElementById("music-status");
  if (!audio || !status) return;
  const read = (key) => { try { return localStorage.getItem(key); } catch { return null; } };
  const save = (key, value) => { try { localStorage.setItem(key, value); } catch {} };
  audio.src = "/media/wald2.mp3";
  audio.volume = 0.3;
  let automaticPause = false;
  const play = () => audio.play().catch(() => {
    status.textContent = "Mit Play Musik einschalten – der Browser erlaubt keinen automatischen Tonstart.";
  });
  audio.addEventListener("play", () => {
    automaticPause = false;
    save("tormentor.music.enabled", "yes");
    status.textContent = "Musik läuft in einer Schleife. Links und Videos pausieren sie.";
  });
  audio.addEventListener("pause", () => {
    if (!automaticPause) save("tormentor.music.enabled", "no");
    status.textContent = "Musik pausiert. Mit Play wieder einschalten.";
  });
  audio.addEventListener("error", () => {
    status.textContent = "Dieser Waldsound konnte nicht geladen werden. Bitte einen anderen auswählen.";
  });
  const pauseForContent = () => {
    automaticPause = true;
    audio.pause();
  };
  document.addEventListener("click", (event) => {
    if (event.target.closest("a[href], [data-video], video")) pauseForContent();
  }, true);
  document.addEventListener("play", (event) => {
    if (event.target !== audio) pauseForContent();
  }, true);
  window.addEventListener("pagehide", pauseForContent);
  if (read("tormentor.music.enabled") !== "no") play();
})();
