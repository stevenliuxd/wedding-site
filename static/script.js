// Years/months/days married since wedding day: 2026-08-08 15:30 (Mountain Time, UTC-06:00)
(function () {
  const weddingDay = new Date('2026-08-08T15:30:00-06:00');
  const $ = (id) => document.getElementById(id);
  const years = $('cd-years'), months = $('cd-months'), days = $('cd-days');
  if (!days) return;

  function tick() {
    const now = new Date();
    let y = now.getFullYear() - weddingDay.getFullYear();
    let m = now.getMonth() - weddingDay.getMonth();
    let d = now.getDate() - weddingDay.getDate();
    if (now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds() <
        weddingDay.getHours() * 3600 + weddingDay.getMinutes() * 60 + weddingDay.getSeconds()) {
      d--;
    }
    if (d < 0) {
      m--;
      d += new Date(now.getFullYear(), now.getMonth(), 0).getDate();
    }
    if (m < 0) {
      y--;
      m += 12;
    }
    y = Math.max(0, y); m = Math.max(0, m); d = Math.max(0, d);
    if (years) years.textContent = String(y);
    if (months) months.textContent = String(m);
    days.textContent = String(d);
  }
  tick();
  setInterval(tick, 60000);
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
