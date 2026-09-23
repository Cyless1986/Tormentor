"use strict";
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-video]");
  if (!button || !/^[A-Za-z0-9_-]{11}$/.test(button.dataset.video)) return;
  const iframe = document.createElement("iframe");
  iframe.src = `https://www.youtube-nocookie.com/embed/${button.dataset.video}?autoplay=1&rel=0`;
  iframe.title = button.getAttribute("aria-label").replace("Video laden: ", "");
  iframe.allow = "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen";
  iframe.allowFullscreen = true;
  iframe.referrerPolicy = "strict-origin-when-cross-origin";
  button.replaceWith(iframe);
});
const cards = Array.from(document.querySelectorAll("[data-feed-card]"));
const more = document.querySelector("[data-feed-more]");
const end = document.querySelector("[data-feed-end]");
let shown = 0;
let showSeen = false;
const seenKey = "tormentor-seen-feed-v1";
let seen = new Set();
try { seen = new Set(JSON.parse(localStorage.getItem(seenKey) || "[]")); } catch (_) {}
const day = new Date().toISOString().slice(0, 10);
const dailyOffset = [...day].reduce((sum, char) => sum + char.charCodeAt(0), 0) % Math.max(cards.length, 1);
if (cards.length > 1) cards.push(...cards.splice(0, dailyOffset));
cards.forEach((card) => {
  if (seen.has(card.dataset.feedId)) card.hidden = true;
  card.querySelector("[data-feed-link]")?.addEventListener("click", () => {
    seen.add(card.dataset.feedId);
    try { localStorage.setItem(seenKey, JSON.stringify([...seen])); } catch (_) {}
  });
});
document.querySelector("[data-feed-show-seen]")?.addEventListener("click", (event) => {
  showSeen = true;
  cards.forEach((card) => { if (seen.has(card.dataset.feedId)) card.hidden = false; });
  event.currentTarget.hidden = true;
});
function showMore() {
  shown = Math.min(shown + 6, cards.length);
  cards.forEach((card, index) => { card.hidden = index >= shown || (!showSeen && seen.has(card.dataset.feedId)); });
  if (more) more.hidden = shown >= cards.length;
  if (end) end.hidden = shown < cards.length;
}
if (cards.length) {
  showMore();
  more?.addEventListener("click", showMore);
  if ("IntersectionObserver" in window && more) {
    new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting) && shown < cards.length) showMore();
    }, { rootMargin: "200px" }).observe(more);
  }
}
