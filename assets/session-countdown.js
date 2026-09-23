"use strict";
document.querySelectorAll('.saber-toggle').forEach(button => {
  button.addEventListener('click', () => {
    const paused = button.closest('.session-sabers').classList.toggle('sabers-paused');
    button.setAttribute('aria-pressed', String(paused));
    button.textContent = paused ? 'Animation fortsetzen' : 'Animation pausieren';
  });
});
function updateSessionCountdown() {
  document.querySelectorAll('[data-session-day]').forEach((node) => {
    if (!node.dataset.sessionTarget) {
      const parts = new Intl.DateTimeFormat('en-CA', {timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
      const value = type => parts.find(p => p.type === type).value;
      const today = Date.UTC(Number(value('year')), Number(value('month'))-1, Number(value('day')));
      const days = Math.round((Date.parse(node.dataset.sessionDay+'T00:00:00Z')-today)/86400000);
      node.textContent = days > 0 ? `Noch ${days} ${days===1?'Tag':'Tage'} · Uhrzeit folgt` : days===0 ? 'Heute ist Sessiontag · Uhrzeit folgt' : 'Termin vergangen · neuer Termin folgt';
      return;
    }
    const ms = Date.parse(node.dataset.sessionTarget)-Date.now();
    if (ms<=0) {node.textContent='Die Startzeit ist erreicht — viel Spaß beim Abenteuer!';return;}
    const mins=Math.floor(ms/60000);
    node.textContent = `${Math.floor(mins/1440)} Tage · ${Math.floor(mins%1440/60)} Std. · ${mins%60} Min.`;
  });
}
updateSessionCountdown();
setInterval(updateSessionCountdown,1000);
