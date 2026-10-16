(() => {
  const form = document.getElementById('character-sheet');
  const status = document.getElementById('sheet-status');
  let dirty = false;
  const options = window.tormentorNavigation ? {signal:window.tormentorNavigation.scope.signal} : undefined;
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
  window.addEventListener('hashchange', pageFromHash, options);
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
  const inventory = form.elements.inventory;
  const rows = document.getElementById('inventory-rows');
  const kinds = {potion: ['Trank', .25], sword: ['Einhandschwert', 1], armor: ['Rüstung', 2], heavy: ['Schwere Rüstung', 3], food: ['Essen', 0], drink: ['Trinken', 0], money: ['Geld', 0], scroll: ['Schriftrollen', null], book: ['Bücher', null], ingredient: ['Zutaten', null], tool: ['Werkzeuge', null], quest: ['Questobjekte', null], other: ['Sonstiges', null]};
  function addItem(item) {
    const row = document.createElement('div');
    row.className = 'inventory-row';
    row.innerHTML = '<label>Gegenstand<input data-field="name" maxlength="120" required></label><label>Art<select data-field="kind"></select></label><label>Menge<input data-field="quantity" type="number" min="1" max="9999" step="1" required></label><label>Slots je Stück<input data-field="slots" type="number" min="0" max="999" step="0.25" required></label><label class="inventory-equipped"><input data-field="equipped" type="checkbox"> Ausgerüstet</label><button type="button">Entfernen</button>';
    const select = row.querySelector('select');
    Object.entries(kinds).forEach(([key, [label]]) => select.add(new Option(label, key)));
    row.querySelectorAll('[data-field]').forEach(input => {
      if (input.type === 'checkbox') input.checked = item[input.dataset.field];
      else input.value = item[input.dataset.field];
    });
    row.querySelector('button').addEventListener('click', () => {row.remove(); form.dispatchEvent(new Event('input'));});
    rows.append(row);
  }
  let inventoryValid = true;
  try { JSON.parse(inventory.value).forEach(addItem); }
  catch { inventoryValid = false; status.textContent = 'Inventardaten konnten nicht geladen werden. Bitte den Bogen neu öffnen.'; }
  document.getElementById('inventory-add').addEventListener('click', () => {
    if (!inventoryValid || rows.children.length >= 200) return;
    addItem({name: '', kind: 'other', quantity: 1, slots: 1, equipped: false});
    rows.lastElementChild.querySelector('input').focus();
    form.dispatchEvent(new Event('input'));
  });
  function calculateInventory() {
    if (!inventoryValid) return;
    let used = 0;
    const items = [...rows.children].map(row => {
      const item = {};
      row.querySelectorAll('[data-field]').forEach(input => {item[input.dataset.field] = input.type === 'checkbox' ? input.checked : input.type === 'number' ? Number(input.value) : input.value;});
      const fixed = kinds[item.kind]?.[1];
      const slotsInput = row.querySelector('[data-field="slots"]');
      slotsInput.readOnly = fixed != null;
      if (fixed != null) {item.slots = fixed; slotsInput.value = fixed;}
      if (!item.equipped) used += item.quantity * item.slots;
      return item;
    });
    inventory.value = JSON.stringify(items);
    const capacity = number('str');
    const display = document.getElementById('inventory-load');
    display.textContent = `${used.toLocaleString('de-DE')} / ${capacity} Slots` + (used > capacity ? ' · Überladen!' : ` · ${(capacity - used).toLocaleString('de-DE')} frei`);
    display.classList.toggle('error', used > capacity);
    const progress = document.getElementById('inventory-progress');
    progress.max = Math.max(1, capacity); progress.value = used;
  }
  function calculate() {
    calculateInventory();
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
  form.addEventListener('input', () => { dirty = true; form.dataset.portalDirty = 'true'; status.textContent = 'Ungespeicherte Änderungen'; calculate(); });
  form.addEventListener('submit', () => { dirty = false; delete form.dataset.portalDirty; });
  window.addEventListener('beforeunload', event => { if (dirty) {event.preventDefault(); event.returnValue = '';} }, options);
  calculate();
})();
