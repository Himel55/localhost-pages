// Edit mode: toggles drag handles on/off, hides the × button to prevent
// fat-finger deletes, and wires up native HTML5 drag-and-drop reordering.
// Dropping a row writes the new order and forces sort to manual.
(function () {
  const { KEYS, saveArray, onEscape } = window.LP;
  const list = document.querySelector('.apps');
  const toggle = document.querySelector('.edit-toggle');
  if (!list || !toggle) return;

  function isEditing() {
    return document.body.classList.contains('editing');
  }

  function setEditing(on) {
    document.body.classList.toggle('editing', on);
    toggle.setAttribute('aria-pressed', String(on));
    toggle.textContent = on ? 'DONE' : 'EDIT';
    list.querySelectorAll('.row').forEach((row) => {
      row.draggable = on;
      // The body is an <a>, which natively drags as a link and hijacks the
      // reorder drag. Disable its draggability while editing so the drag
      // bubbles up to the row from anywhere on the card.
      const body = row.querySelector('.body');
      if (body) body.draggable = !on;
    });
  }

  toggle.addEventListener('click', () => setEditing(!isEditing()));

  onEscape(60, () => {
    if (!isEditing()) return false;
    setEditing(false);
    return true;
  });

  // Drag-and-drop reorder. Native HTML5 DnD is enough for in-list moves.
  let dragging = null;

  list.addEventListener('dragstart', (e) => {
    if (!isEditing()) return;
    const row = e.target.closest('.row');
    if (!row) return;
    dragging = row;
    row.classList.add('drag-source');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', row.dataset.name);
  });

  list.addEventListener('dragend', (e) => {
    const row = e.target.closest('.row');
    if (row) row.classList.remove('drag-source');
    dragging = null;
    list.querySelectorAll('.drag-over').forEach((r) => r.classList.remove('drag-over'));
  });

  list.addEventListener('dragover', (e) => {
    if (!dragging) return;
    e.preventDefault();
    const target = e.target.closest('.row');
    if (!target || target === dragging) return;
    const rect = target.getBoundingClientRect();
    const before = (e.clientY - rect.top) < rect.height / 2;
    list.querySelectorAll('.drag-over').forEach((r) => r.classList.remove('drag-over'));
    target.classList.add('drag-over');
    if (before) target.before(dragging);
    else target.after(dragging);
  });

  list.addEventListener('drop', (e) => {
    e.preventDefault();
    list.querySelectorAll('.drag-over').forEach((r) => r.classList.remove('drag-over'));
    if (!dragging) return;
    const order = Array.from(list.querySelectorAll('.row')).map((r) => r.dataset.name);
    saveArray(KEYS.order, order);
    // Switch to manual sort so the new order sticks on next reload.
    window.LP.sort?.set('manual');
  });
})();
