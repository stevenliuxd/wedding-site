// Countdown to wedding day: 2026-08-08 15:30 (Mountain Time, UTC-06:00)
(function () {
  const target = new Date('2026-08-08T15:30:00-06:00').getTime();
  const $ = (id) => document.getElementById(id);
  const days = $('cd-days'), hours = $('cd-hours'), mins = $('cd-mins'), secs = $('cd-secs');
  if (!days) return;

  const pad = (n) => String(Math.max(0, n)).padStart(2, '0');

  function tick() {
    const diff = target - Date.now();
    if (diff <= 0) {
      days.textContent = '00'; hours.textContent = '00';
      mins.textContent = '00'; secs.textContent = '00';
      return;
    }
    const d = Math.floor(diff / 86400000);
    const h = Math.floor((diff % 86400000) / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    days.textContent = pad(d);
    hours.textContent = pad(h);
    mins.textContent = pad(m);
    secs.textContent = pad(s);
  }
  tick();
  setInterval(tick, 1000);
})();

// RSVP form: dynamic guest blocks and conditional menu sections
(function () {
  const list = document.getElementById('guest-list');
  if (!list) return;

  const addBtn = document.getElementById('add-guest');
  const MAX_GUESTS = 6;

  function renumber() {
    const blocks = list.querySelectorAll('.guest-block');
    blocks.forEach((block, idx) => {
      const num = idx + 1;
      block.querySelector('.guest-title').textContent = `Guest ${num}`;
      block.querySelectorAll('[data-name]').forEach((el) => {
        const base = el.dataset.name;
        el.name = `guests[${idx}][${base}]`;
        const id = `g${idx}_${base}`;
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') {
          el.id = id;
          const lbl = block.querySelector(`label[data-for="${base}"]`);
          if (lbl) lbl.htmlFor = id;
        }
      });
      block.querySelectorAll('input[type="radio"]').forEach((radio) => {
        const group = radio.dataset.group;
        radio.name = `guests[${idx}][${group}]`;
      });
      const removeBtn = block.querySelector('.guest-remove');
      if (removeBtn) removeBtn.style.display = blocks.length > 1 ? '' : 'none';
    });
    if (addBtn) addBtn.disabled = blocks.length >= MAX_GUESTS;
  }

  function wireBlock(block) {
    block.querySelectorAll('input[data-group="attending"]').forEach((radio) => {
      radio.addEventListener('change', () => {
        const menu = block.querySelector('.menu-section');
        if (!menu) return;
        const yes = block.querySelector('input[data-group="attending"][value="yes"]');
        if (yes && yes.checked) {
          menu.classList.add('visible');
          menu.querySelectorAll('input[type="radio"]').forEach((r) => r.required = true);
        } else {
          menu.classList.remove('visible');
          menu.querySelectorAll('input[type="radio"]').forEach((r) => { r.required = false; r.checked = false; });
        }
      });
    });
    const removeBtn = block.querySelector('.guest-remove');
    if (removeBtn) {
      removeBtn.addEventListener('click', () => {
        block.remove();
        renumber();
      });
    }
  }

  // Wire the initial block
  list.querySelectorAll('.guest-block').forEach(wireBlock);
  renumber();

  if (addBtn) {
    const template = document.getElementById('guest-template');
    addBtn.addEventListener('click', () => {
      const blocks = list.querySelectorAll('.guest-block');
      if (blocks.length >= MAX_GUESTS) return;
      const clone = template.content.firstElementChild.cloneNode(true);
      list.appendChild(clone);
      wireBlock(clone);
      renumber();
      clone.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  }
})();
