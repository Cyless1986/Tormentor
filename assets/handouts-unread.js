(() => {
  const badge = document.getElementById('handouts-unread');
  const link = document.getElementById('handouts-link');
  if (!badge || !link) return;
  let busy = false;
  async function update() {
    if (document.hidden || busy) return;
    busy = true;
    try {
      for (const card of document.querySelectorAll('.handout-card[open][data-handout-read="0"]')) {
        const response = await fetch('/handouts/read', {
          method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},
          body:new URLSearchParams({id:card.dataset.handoutId,version:card.dataset.handoutVersion})
        });
        if (response.ok && !response.redirected) {
          card.dataset.handoutRead='1';
          card.querySelector('.handout-new')?.remove();
        } else if (response.status===409) {
          let note=card.querySelector('.handout-refresh');
          if (!note) {
            note=document.createElement('p');
            note.className='handout-refresh';
            const reload=document.createElement('a');
            reload.href='/handouts'; reload.textContent='Dieses Handout wurde aktualisiert. Neue Fassung laden.';
            note.append(reload); card.append(note);
          }
        }
      }
      const response=await fetch('/handouts/unread',{cache:'no-store'});
      if (!response.ok || response.redirected) throw new Error();
      const count=Number(await response.text());
      if (!Number.isInteger(count) || count<0) throw new Error();
      badge.textContent=count ? String(count) : '';
      badge.hidden=count===0;
      link.setAttribute('aria-label',count ? 'Handouts: '+count+' ungelesen' : 'Handouts');
      link.title=count ? count+' ungelesene Handouts' : 'Keine ungelesenen Handouts';
    } catch (_) { link.title='Handout-Status aktuell nicht abrufbar'; }
    finally { busy=false; }
  }
  document.querySelectorAll('.handout-card').forEach(card=>card.addEventListener('toggle',update));
  document.addEventListener('visibilitychange',update);
  window.setInterval(update,3000);
  update();
})();
