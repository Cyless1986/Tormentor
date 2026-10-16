(() => {
  document.querySelectorAll('[data-portrait-url]').forEach(card => {
    const button = card.querySelector('[data-portrait-upload]');
    const input = card.querySelector('[data-portrait-file]');
    const status = card.querySelector('[data-portrait-status]');
    button.addEventListener('click', async () => {
      const file = input.files[0];
      if (!file) { status.textContent = 'Bitte zuerst ein Bild auswählen.'; return; }
      if (file.size > 8 * 1024 * 1024 || !file.size) { status.textContent = 'Bitte ein Bild bis 8 MB auswählen.'; return; }
      button.disabled = true;
      status.textContent = 'Bild wird hochgeladen …';
      try {
        const response = await fetch(card.dataset.portraitUrl, {method:'POST', headers:{'Content-Type':'application/octet-stream'}, body:file});
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Upload fehlgeschlagen.');
        const image = card.querySelector('[data-portrait-image]');
        image.src = card.dataset.portraitUrl + '?v=' + Date.now();
        image.hidden = false;
        card.querySelector('[data-portrait-empty]').hidden = true;
        input.value = '';
        button.textContent = 'Bild ersetzen';
        status.textContent = 'Bild gespeichert. Deine übrigen Eingaben bleiben erhalten.';
      } catch (error) { status.textContent = error.message || 'Upload fehlgeschlagen. Bitte erneut versuchen.'; }
      finally { button.disabled = false; }
    });
  });
})();
