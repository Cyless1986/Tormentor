(() => {
  const badge = document.getElementById('chat-unread');
  const link = document.getElementById('chat-link');
  if (!badge || !link) return;
  const title = document.title;
  let busy = false;
  async function update() {
    if (document.hidden || busy) return;
    busy = true;
    try {
      const feed = document.getElementById('chat-feed');
      if (feed) {
        let through = 0;
        feed.querySelectorAll('[data-message-id]').forEach(el => {
          through = Math.max(through, Number(el.dataset.messageId));
        });
        if (through) {
          const saved = await fetch('/messages/read', {
            method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: 'through=' + through
          });
          if (!saved.ok || saved.redirected) throw new Error();
        }
      }
      const response = await fetch('/messages/unread', {cache: 'no-store'});
      if (!response.ok || response.redirected) throw new Error();
      const count = Number(await response.text());
      if (!Number.isInteger(count) || count < 0) throw new Error();
      badge.textContent = count ? String(count) : '';
      badge.hidden = count === 0;
      link.setAttribute('aria-label', count ? 'Nachrichten: ' + count + ' ungelesen' : 'Nachrichten');
      link.title = count ? count + ' ungelesene Nachrichten' : 'Keine ungelesenen Nachrichten';
      document.title = count ? '(' + count + ') ' + title : title;
    } catch (_) {
      link.title = 'Nachrichtenstatus aktuell nicht abrufbar';
    } finally { busy = false; }
  }
  document.addEventListener('visibilitychange', update);
  document.addEventListener('chat-updated', update);
  window.setInterval(update, 3000);
  update();
})();
