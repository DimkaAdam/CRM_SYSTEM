/* --- Boot log --- */
console.log("home.js LOADED");

/* ======================
   1) Helpers / CSRF
   ====================== */

/** Вернуть cookie по имени */
function getCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return m ? m.pop() : "";
}

/** Глобальный CSRF-токен из cookie */
const csrftoken = getCookie('csrftoken');

/* ======================
   2) Store в <script id="daily-store">
   ====================== */

function getStoreEl() {
  let el = document.getElementById('daily-store');
  if (!el) {
    // создаём "тихий" стор, чтобы код не падал, даже если блока нет в шаблоне
    el = document.createElement('script');
    el.type = 'application/json';
    el.id = 'daily-store';
    el.textContent = '{}';
    document.body.appendChild(el);
  }
  return el;
}

function getStore() {
  const el = getStoreEl();
  try { return JSON.parse(el.textContent || '{}'); } catch { return {}; }
}

function setStore(obj) {
  const el = getStoreEl();
  el.textContent = JSON.stringify(obj);
}

/* ======================
   2.1) Деловая дата (19:00 отсечка)
   ====================== */

/** Превращает ISO-дату записи в "деловую" дату YYYY-MM-DD с границей 19:00 */
function toBusinessDay(iso) {
  if (!iso) return 'unknown';
  const d = new Date(iso);
  const y = d.getFullYear(), m = d.getMonth(), day = d.getDate();
  const hour = d.getHours();
  // если время до 19:00 — это еще вчерашний деловой день
  const base = new Date(y, m, day - (hour < 0 || (hour === 0 && minute < 1) ? 1 : 0));
  const YY = base.getFullYear();
  const MM = String(base.getMonth() + 1).padStart(2, '0');
  const DD = String(base.getDate()).padStart(2, '0');
  return `${YY}-${MM}-${DD}`;
}

/** Текущая деловая дата "сейчас" */
function currentBusinessDay() {
  return toBusinessDay(new Date().toISOString());
}

/* ======================
   2.2) Группировка по датам YYYY-MM-DD
   ====================== */

function groupByDate(items) {
  const out = {};
  for (const r of items) {
    // приоритетно берём r.report_day, иначе считаем из r.date
    const d = (r.report_day ? r.report_day.slice(0,10) : toBusinessDay(r.date)) || 'unknown';
    if (!out[d]) out[d] = { items: [], totals: { gross: 0, net: 0, count: 0 } };
    out[d].items.push(r);
    out[d].totals.gross += +r.gross;
    out[d].totals.net += +r.net;
    out[d].totals.count += 1;
  }
  return out;
}

function upsertItemToStore(item) {
  // гарантируем деловую дату
  const bd = (item.report_day || toBusinessDay(item.date || new Date().toISOString())).slice(0,10) || 'unknown';
  const store = getStore();
  if (!store[bd]) store[bd] = { items: [], totals: { gross: 0, net: 0, count: 0 } };
  const idx = store[bd].items.findIndex(x => x.id === item.id);
  if (idx === -1) {
    store[bd].items.push(item);
    store[bd].totals.gross += +item.gross;
    store[bd].totals.net += +item.net;
    store[bd].totals.count += 1;
  } else {
    const old = store[bd].items[idx];
    store[bd].totals.gross += (+item.gross - +old.gross);
    store[bd].totals.net += (+item.net - +old.net);
    store[bd].items[idx] = item;
  }
  setStore(store);
  renderAllDays();
}

function removeItemFromStore(item) {
  const bd = (item.report_day || toBusinessDay(item.date)).slice(0,10) || 'unknown';
  const store = getStore();
  if (!store[bd]) return;
  const idx = store[bd].items.findIndex(x => x.id === item.id);
  if (idx === -1) return;
  const old = store[bd].items[idx];
  store[bd].items.splice(idx, 1);
  store[bd].totals.gross -= +old.gross;
  store[bd].totals.net -= +old.net;
  store[bd].totals.count -= 1;
  if (store[bd].items.length === 0) delete store[bd];
  setStore(store);
  renderAllDays();
}

/* ======================
   3) Справочники (для inline-редактирования)
   ====================== */

const MATERIALS = ["Flexible Plastic", "Mix Container", "Baled Cardboard"];
const SUPPLIERS = ["Bottle Depot","Hannam", "Inno Food", "Meridian", "T-Brothers", "Zoom Books", "Green House"];

/* ======================
   4) Загрузка начальных данных
   ====================== */

document.addEventListener("DOMContentLoaded", reloadFromDB);

/** Границы месяца YYYY, M -> ISO from/to */
function monthBounds(y, m /* 0..11 */) {
  const from = new Date(y, m, 1, 0, 0, 0);
  const to   = new Date(y, m + 1, 0, 23, 59, 59); // последний день месяца 23:59:59
  const iso = d => new Date(d.getTime() - d.getTimezoneOffset()*60000).toISOString().slice(0,19);
  return { from: iso(from), to: iso(to) };
}

/**
 * Грузим историю «за все дни».
 * Т.к. на бэке есть from/to — идём помесячно назад до N месяцев,
 * и останавливаемся, если подряд встретили несколько пустых месяцев.
 */
async function loadFullHistory(maxMonths = 36, emptyBreak = 6) {
  const now = new Date();
  let y = now.getFullYear();
  let m = now.getMonth(); // 0..11

  const all = [];
  const seen = new Set();              // <- здесь копим уже встреченные id
  let emptyStreak = 0;
  let noNewStreak = 0;                 // <- подряд месяцев без новых записей

  const { from: debugFrom, to: debugTo } = monthBounds(y, m); // можно логировать при желании

  for (let i = 0; i < maxMonths; i++) {
    const { from, to } = monthBounds(y, m);
    const url = `/scales/api/received/?from=${from}&to=${to}`;
    const r = await fetch(url, { credentials: "same-origin" });
    if (!r.ok) break;

    const j = await r.json();
    const items = (j.items || []);

    // посчитаем, сколько реально новых записей добавили
    let added = 0;
    for (const it of items) {
      const id = String(it.id ?? `${it.material}|${it.tag}|${it.date}`);
      if (seen.has(id)) continue;      // уже добавляли — пропускаем
      seen.add(id);
      all.push(it);
      added += 1;
    }

    if (items.length === 0) {
      emptyStreak += 1;
      if (emptyStreak >= emptyBreak) break;
    } else {
      emptyStreak = 0;
    }

    // если месяц ничего нового не дал (бэкенд вернул тот же массив),
    // считаем это «нет новинок»; много таких подряд — выходим
    if (added === 0) {
      noNewStreak += 1;
      if (noNewStreak >= 3) break;     // 3 месяца подряд без новых -> стоп
    } else {
      noNewStreak = 0;
    }

    // шаг на месяц назад
    m -= 1;
    if (m < 0) { m = 11; y -= 1; }
  }

  const todayBD = currentBusinessDay();
  return all
    .map(it => ({ ...it, report_day: it.report_day || toBusinessDay(it.date) }))
    .filter(it => (it.report_day || '').slice(0,10) !== todayBD);
}

async function reloadFromDB() {
  try {
    // ВЕРХ: только текущие записи (как и просил — не трогаем)
    const topRes = await fetch("/scales/api/received/?period=today", { credentials: "same-origin" });
    const topJson = await topRes.json();
    const topItems = topJson.items || [];
    const tbody = document.querySelector("#report-table tbody");
    tbody.innerHTML = "";
    topItems.forEach(appendRow);
    recalcTotals();

    // НИЗ: вся история за все дни (много месяцев назад)
    const allItems = await loadFullHistory(36, 6); // до 3 лет, остановка после 6 пустых месяцев подряд
    setStore(groupByDate(allItems));
    renderAllDays();
  } catch (e) {
    console.error("reloadFromDB failed:", e);
  }
}

/* ======================
   5) Создание записи
   ====================== */

async function addRow() {
  const material = document.getElementById("material").value.trim();
  const gross = parseFloat(document.getElementById("gross").value.trim());
  const net = parseFloat(document.getElementById("net").value.trim());
  const supplier = document.getElementById("supplier").value.trim();
  const tag = document.getElementById("tag").value.trim();

  if (!material || isNaN(gross) || isNaN(net) || !supplier || !tag) {
    alert("Please fill all fields (weights must be numbers).");
    return;
  }

  // Оптимистичная вставка (по желанию)
  const tmp = {
    id: "tmp_" + Date.now(),
    date: new Date().toISOString(),
    material, gross, net, supplier, tag
  };
  appendRow(tmp);
  recalcTotals();

  try {
    const r = await fetch("/scales/api/received/create/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken
      },
      body: JSON.stringify({ material, gross, net, supplier, tag })
    });
    if (!r.ok) throw new Error("Save failed");
    await reloadFromDB(); // подтянуть реальные id/даты
  } catch (e) {
    console.error(e);
    alert("Save failed. Check server.");
  }

  document.getElementById("gross").value = "";
  document.getElementById("net").value = "";
  document.getElementById("tag").value = "";
  document.getElementById("gross").focus();
}

/* ======================
   6) Рендер строки
   ====================== */

function appendRow({ id, date, material, gross, net, supplier, tag }) {
  const tbody = document.querySelector("#report-table tbody");
  const tr = document.createElement("tr");
  if (id) tr.dataset.id = id;
  if (date) tr.dataset.date = date;
  tr.innerHTML = `
    <td data-col="material">${material}</td>
    <td data-col="gross">${Number(gross).toFixed(1)}</td>
    <td data-col="net">${Number(net).toFixed(1)}</td>
    <td data-col="supplier">${supplier}</td>
    <td data-col="tag">${tag}</td>
    <td class="action-row" style="text-align:right">
      <button class="action-btn" onclick="startEdit(this)">Edit</button>
      <button class="action-btn" onclick="deleteRow(this)">Delete</button>
    </td>`;
  tbody.appendChild(tr);
}

/* ======================
   7) Редактирование
   ====================== */

function selectHTML(options, current) {
  return `<select style="width:100%">${options.map(opt =>
    `<option ${opt === current ? 'selected' : ''}>${opt}</option>`).join("")}</select>`;
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}
function escapeAttr(s) {
  return (s || "").replace(/"/g,'&quot;').replace(/'/g,"&#39;");
}

function startEdit(btn) {
  const tr = btn.closest("tr");
  if (tr.dataset.editing === "1") return;
  tr.dataset.editing = "1";

  const material = tr.querySelector("[data-col='material']").textContent;
  const gross = tr.querySelector("[data-col='gross']").textContent;
  const net = tr.querySelector("[data-col='net']").textContent;
  const supplier = tr.querySelector("[data-col='supplier']").textContent;
  const tag = tr.querySelector("[data-col='tag']").textContent;

  tr.querySelector("[data-col='material']").innerHTML = selectHTML(MATERIALS, material);
  tr.querySelector("[data-col='gross']").innerHTML = `<input type="number" step="0.1" value="${gross}" style="width:100%">`;
  tr.querySelector("[data-col='net']").innerHTML   = `<input type="number" step="0.1" value="${net}" style="width:100%">`;
  tr.querySelector("[data-col='supplier']").innerHTML = selectHTML(SUPPLIERS, supplier);
  tr.querySelector("[data-col='tag']").innerHTML = `<input type="text" value="${escapeHtml(tag)}" style="width:100%">`;

  tr.querySelector(".action-row").innerHTML = `
    <button class="action-btn" onclick="saveEdit(this)">Save</button>
    <button class="action-btn" onclick="cancelEdit(this,'${escapeAttr(material)}','${gross}','${net}','${escapeAttr(supplier)}','${escapeAttr(tag)}')">Cancel</button>`;
}

function cancelEdit(btn, material, gross, net, supplier, tag) {
  const tr = btn.closest("tr");
  tr.dataset.editing = "0";
  tr.querySelector("[data-col='material']").textContent = material;
  tr.querySelector("[data-col='gross']").textContent = Number(gross).toFixed(1);
  tr.querySelector("[data-col='net']").textContent = Number(net).toFixed(1);
  tr.querySelector("[data-col='supplier']").textContent = supplier;
  tr.querySelector("[data-col='tag']").textContent = tag;
  tr.querySelector(".action-row").innerHTML = `
    <button class="action-btn" onclick="startEdit(this)">Edit</button>
    <button class="action-btn" onclick="deleteRow(this)">Delete</button>`;
}

async function saveEdit(btn) {
  const tr = btn.closest("tr");
  const id = tr.dataset.id;
  if (!id || String(id).startsWith("tmp_")) { alert("Item not saved yet."); return; }

  const material = tr.querySelector("[data-col='material'] select").value.trim();
  const gross = parseFloat(tr.querySelector("[data-col='gross'] input").value.trim());
  const net = parseFloat(tr.querySelector("[data-col='net'] input").value.trim());
  const supplier = tr.querySelector("[data-col='supplier'] select").value.trim();
  const tag = tr.querySelector("[data-col='tag'] input").value.trim();

  if (!material || isNaN(gross) || isNaN(net) || !supplier || !tag) {
    alert("Fill all fields correctly.");
    return;
  }

  try {
    const r = await fetch(`/scales/api/received/${id}/update/`, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken
      },
      body: JSON.stringify({ material, gross, net, supplier, tag })
    });
    if (!r.ok) throw new Error("Update failed");

    const { item } = await r.json();
    if (!item.date) item.date = tr.dataset.date || new Date().toISOString();

    tr.dataset.editing = "0";
    tr.dataset.date = item.date;
    tr.querySelector("[data-col='material']").textContent = item.material;
    tr.querySelector("[data-col='gross']").textContent = Number(item.gross).toFixed(1);
    tr.querySelector("[data-col='net']").textContent   = Number(item.net).toFixed(1);
    tr.querySelector("[data-col='supplier']").textContent = item.supplier;
    tr.querySelector("[data-col='tag']").textContent = item.tag;
    tr.querySelector(".action-row").innerHTML = `
      <button class="action-btn" onclick="startEdit(this)">Edit</button>
      <button class="action-btn" onclick="deleteRow(this)">Delete</button>`;

    upsertItemToStore(item);
    recalcTotals();
  } catch (e) {
    console.error(e);
    alert("Update failed.");
  }
}

/* ======================
   8) Удаление
   ====================== */

async function deleteRow(btn) {
  const tr = btn.closest("tr");
  const id = tr.dataset.id;

  // временная строка — просто убрать локально
  if (!id || String(id).startsWith("tmp_")) {
    const deleted = {
      id: id || "tmp",
      date: tr.dataset.date || new Date().toISOString(),
      gross: parseFloat(tr.querySelector("[data-col='gross']").textContent) || 0,
      net: parseFloat(tr.querySelector("[data-col='net']").textContent) || 0
    };
    tr.remove();
    removeItemFromStore(deleted);
    recalcTotals();
    return;
  }

  if (!confirm("Delete this row?")) return;

  try {
    const r = await fetch(`/scales/api/received/${id}/delete/`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-CSRFToken": csrftoken }
    });
    if (!r.ok) throw new Error("Delete failed");

    const deleted = {
      id,
      date: tr.dataset.date || new Date().toISOString(),
      gross: parseFloat(tr.querySelector("[data-col='gross']").textContent) || 0,
      net: parseFloat(tr.querySelector("[data-col='net']").textContent) || 0
    };
    tr.remove();
    removeItemFromStore(deleted);
    recalcTotals();
  } catch (e) {
    console.error(e);
    alert("Delete failed.");
  }
}

/* ======================
   9) Итоги таблицы
   ====================== */

function recalcTotals() {
  const grossTotal = [...document.querySelectorAll("#report-table tbody tr td:nth-child(2)")]
    .reduce((s, td) => s + (parseFloat(td.textContent) || 0), 0);
  const netTotal = [...document.querySelectorAll("#report-table tbody tr td:nth-child(3)")]
    .reduce((s, td) => s + (parseFloat(td.textContent) || 0), 0);

  let tfoot = document.querySelector("#report-table tfoot");
  if (!tfoot) {
    tfoot = document.createElement("tfoot");
    document.getElementById("report-table").appendChild(tfoot);
  }
  tfoot.innerHTML = `
    <tr>
      <th style="text-align:right">Totals:</th>
      <th>${grossTotal.toFixed(1)}</th>
      <th>${netTotal.toFixed(1)}</th>
      <th colspan="3"></th>
    </tr>`;
}

/* ======================
   10) История по дням (карточки)
   ====================== */

function fmt(n) { return Number(n).toFixed(1); }
function humanDate(iso) { try { return new Date(iso).toLocaleDateString(); } catch { return iso; } }

function renderAllDays() {
  const body = document.getElementById('history-body');
  const statsEl = document.getElementById('history-stats');
  if (!body || !statsEl) return; // если блоков нет (например, для рабочих), выходим тихо

  const store = getStore();
  body.innerHTML = '';

  let totalNet = 0, totalCount = 0;
  for (const d of Object.keys(store)) {
    totalNet += store[d].totals.net;
    totalCount += store[d].totals.count;
  }
  statsEl.textContent = `Total net: ${Number(totalNet).toFixed(1)} kg • records: ${totalCount}`;

  const days = Object.keys(store).sort((a, b) => b.localeCompare(a));
  for (const d of days) {
    const day = store[d];
    const card = document.createElement('div');
    card.className = 'day-card';

    const top = document.createElement('div');
    top.className = 'day-row';
    const left = document.createElement('div');
    left.className = 'day-date';
    left.textContent = humanDate(d);
    const right = document.createElement('div');
    right.className = 'badges';
    const b1 = document.createElement('div'); b1.className = 'badge'; b1.textContent = `Net: ${fmt(day.totals.net)} kg`;
    const b2 = document.createElement('div'); b2.className = 'badge'; b2.textContent = `Items: ${day.totals.count}`;
    right.appendChild(b1); right.appendChild(b2);
    top.appendChild(left); top.appendChild(right);
    card.appendChild(top);

    card.appendChild(document.createElement('div')).className = 'divider';

    const grid = document.createElement('div');
    grid.className = 'day-list';
    grid.innerHTML = `
      <div class="h">Material</div>
      <div class="h">Net</div>
      <div class="h">Supplier</div>
      <div class="h">Tag</div>
    `;
    for (const r of day.items) {
      grid.insertAdjacentHTML('beforeend', `
        <div class="c">${r.material}</div>
        <div class="c">${fmt(r.net)} kg</div>
        <div class="c">${r.supplier}</div>
        <div class="c">#${r.tag}</div>
      `);
    }
    card.appendChild(grid);
    body.appendChild(card);
  }
}

/* ======================
   11) Экспорт в window
   ====================== */

Object.assign(window, {
  addRow,
  startEdit,
  saveEdit,
  deleteRow
});
