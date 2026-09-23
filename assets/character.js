(() => {
  const form = document.getElementById('character-sheet');
  const status = document.getElementById('sheet-status');
  let dirty = false;
  const panels = [...form.querySelectorAll('.sheet-panel')];
  const links = [...form.querySelectorAll('.sheet-tabs a')];
  const previous = document.getElementById('sheet-prev');
  const next = document.getElementById('sheet-next');
  let current = 0;
  function showPage(index, focus = false) {
    current = Math.max(0, Math.min(panels.length - 1, index));
    panels.forEach((panel, i) => { panel.hidden = i !== current; });
    links.forEach((link, i) => {
      if (i === current) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    previous.disabled = current === 0;
    next.disabled = current === panels.length - 1;
    document.getElementById('sheet-page-count').textContent = `Seite ${current + 1} von ${panels.length}`;
    if (focus) {
      const heading = panels[current].querySelector('h2');
      heading.tabIndex = -1;
      heading.focus({preventScroll: true});
      heading.scrollIntoView({block: 'start'});
    }
  }
  function pageFromHash() {
    const index = panels.findIndex(panel => '#' + panel.id === location.hash);
    showPage(index < 0 ? 0 : index);
  }
  links.forEach((link, index) => link.addEventListener('click', event => {
    event.preventDefault();
    history.replaceState(null, '', link.hash);
    showPage(index);
  }));
  function turnPage(delta) {
    showPage(current + delta, true);
    history.replaceState(null, '', '#' + panels[current].id);
  }
  previous.addEventListener('click', () => turnPage(-1));
  next.addEventListener('click', () => turnPage(1));
  window.addEventListener('hashchange', pageFromHash);
  form.addEventListener('invalid', event => {
    const panel = event.target.closest('.sheet-panel');
    if (panel) showPage(panels.indexOf(panel));
    const details = event.target.closest('details');
    if (details) details.open = true;
  }, true);
  form.querySelector('.sheet-paging').hidden = false;
  pageFromHash();
  const number = key => Number(form.elements[key].value) || 0;
  const signed = value => (value >= 0 ? '+' : '') + value;
  const mod = key => Math.floor((number(key) - 10) / 2);
  function calculate() {
    document.getElementById('hero-name').textContent = form.elements.namedItem('name').value.trim() || 'Deine Legende beginnt';
    const proficiency = 2 + Math.floor((Math.max(1, Math.min(20, Number(form.dataset.level))) - 1) / 4);
    document.getElementById('proficiency').textContent = signed(proficiency);
    ['str', 'dex', 'con', 'int', 'wis', 'cha'].forEach(key => {
      document.getElementById('mod-' + key).textContent = signed(mod(key));
      document.getElementById('save-' + key).textContent = signed(mod(key) + number('save_' + key) * proficiency);
    });
    form.querySelectorAll('[data-skill]').forEach(el => {
      el.textContent = signed(mod(el.dataset.ability) + number(el.dataset.skill) * proficiency);
    });
    document.getElementById('initiative-total').textContent = signed(mod('dex') + number('initiative'));
    document.getElementById('passive').textContent = 10 + mod('wis') + number('perception') * proficiency;
    const ability = form.elements.spell_ability.value;
    document.getElementById('spell-dc').textContent = ability ? 8 + mod(ability) + proficiency : '–';
    document.getElementById('spell-attack').textContent = ability ? signed(mod(ability) + proficiency) : '–';
  }
  form.addEventListener('input', () => { dirty = true; status.textContent = 'Ungespeicherte Änderungen'; calculate(); });
  form.addEventListener('submit', () => { dirty = false; });
  window.addEventListener('beforeunload', event => { if (dirty) {event.preventDefault(); event.returnValue = '';} });
  calculate();
})();
