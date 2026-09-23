(() => {
  const feed = document.getElementById('chat-feed');
  const status = document.getElementById('chat-status');
  let previous = feed.innerHTML;
  function dates() {
    feed.querySelectorAll('time').forEach(el => {
      el.textContent = new Date(el.dateTime).toLocaleString('de-DE');
    });
  }
  dates();
  async function refresh() {
    try {
      if (!document.hidden) {
        const response = await fetch('/messages/feed', {cache: 'no-store'});
        if (!response.ok || response.redirected) throw new Error();
        const content = await response.text();
        if (content !== previous) {
          previous = content;
          feed.innerHTML = content;
          dates();
          status.textContent = 'Neue Nachricht eingegangen.';
        } else status.textContent = 'Verbunden · automatische Aktualisierung alle 3 Sekunden.';
        document.dispatchEvent(new Event('chat-updated'));
      }
    } catch (_) {
      status.textContent = 'Verbindung unterbrochen oder Anmeldung abgelaufen. Erneuter Versuch in 3 Sekunden; bei Bedarf neu anmelden.';
    } finally { window.setTimeout(refresh, 3000); }
  }
  window.setTimeout(refresh, 3000);
})();
