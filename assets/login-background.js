"use strict";
const background = document.getElementById("login-background");
const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
function updateBackground() {
  if (motion.matches) {
    background.pause();
    background.removeAttribute("src");
    background.load();
    return;
  }
  background.src = "/media/login-tavern-loop.mp4";
  background.muted = true;
  background.play().catch(() => {});
}
motion.addEventListener("change", updateBackground);
updateBackground();
