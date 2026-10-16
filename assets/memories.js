(() => {
  const form = document.getElementById('memory-upload');
  if (form) form.addEventListener('submit', event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const file = form.elements.memory.files[0];
    const status = document.getElementById('memory-status');
    const progress = document.getElementById('memory-progress');
    const button = form.querySelector('button[type=submit]');
    const types = {jpg:'image/jpeg',jpeg:'image/jpeg',png:'image/png',webp:'image/webp',gif:'image/gif',mp4:'video/mp4',webm:'video/webm'};
    const mime = types[file.name.split('.').pop().toLowerCase()] || file.type;
    const limit = mime.startsWith('image/') ? 25 : 250;
    if (!Object.values(types).includes(mime)) { status.textContent = 'Bitte JPG, PNG, WebP, GIF, MP4 oder WebM auswählen.'; return; }
    if (!file.size || file.size > limit * 1024 * 1024) { status.textContent = 'Die Datei darf bis ' + limit + ' MB groß sein.'; return; }
    button.disabled = true;
    progress.hidden = false;
    progress.value = 0;
    status.textContent = 'Upload startet … Bitte diese Seite geöffnet lassen.';
    const request = new XMLHttpRequest();
    request.open('POST','/dm/memories/upload');
    request.timeout = 30 * 60 * 1000;
    request.setRequestHeader('Content-Type',mime);
    request.setRequestHeader('X-Memory-Title',encodeURIComponent(form.elements.title.value.trim()));
    request.setRequestHeader('X-Memory-Caption',encodeURIComponent(form.elements.caption.value.trim()));
    request.setRequestHeader('X-Memory-Date',encodeURIComponent(form.elements.session_date.value));
    request.upload.onprogress = e => {
      if (e.lengthComputable) {
        progress.value = Math.round(e.loaded / e.total * 100);
        status.textContent = progress.value < 100 ? 'Wird hochgeladen … ' + progress.value + ' %' : 'Datei wird geprüft und gespeichert …';
      }
    };
    const fail = message => { button.disabled = false; progress.hidden = true; status.textContent = message; };
    request.onload = () => {
      let result;
      try { result = JSON.parse(request.responseText); } catch (_) {}
      if (request.status === 201) { location.assign('/memories'); return; }
      fail(result?.error || 'Upload fehlgeschlagen. Bitte Anmeldung prüfen und erneut versuchen.');
    };
    request.onerror = () => fail('Verbindung unterbrochen. Bitte erneut versuchen.');
    request.ontimeout = () => fail('Der Upload hat zu lange gedauert. Bitte erneut versuchen.');
    request.send(file);
  });
  document.querySelectorAll('.memory-remove').forEach(form => form.addEventListener('submit',event => {
    if (!confirm('Diese Erinnerung für alle entfernen?')) event.preventDefault();
  }));
})();
