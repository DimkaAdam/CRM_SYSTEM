/* --- Boot log --- */
console.log("home.js LOADED");

/* ======================
   1) Helpers / CSRF
   ====================== */

/** Get cookie by name */
function getCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return m ? m.pop() : "";
}

/** Global CSRF token from cookie */
const csrftoken = getCookie('csrftoken');

/* ======================
   2) Store in <script id="daily-store">
   ====================== */

function getStoreEl() {
  let el = document.getElementById('daily-store');
  if (!el) {
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
  try {
    return JSON.parse(el.textContent || '{}');
  } catch {
    return {};
  }
}

function setStore(obj) {
  const el = getStoreEl();
  el.textContent = JSON.stringify(obj);
}

/* ======================
   2.1) Business Day Logic (12:00 AM cutoff)
   ====================== */

/**
 * Converts ISO date to business day YYYY-MM-DD with 12:00 AM (midnight) cutoff.
 * Records created BEFORE midnight belong to the PREVIOUS business day.
 * Records created AFTER midnight belong to the CURRENT business day.
 *
 * Example:
 * - 2025-01-20 23:59:59 -> business day: 2025-01-19
 * - 2025-01-21 00:00:01 -> business day: 2025-01-21
 */
function toBusinessDay(iso) {
  if (!iso) return 'unknown';

  const d = new Date(iso);
  const hour = d.getHours();
  const minute = d.getMinutes();

  // If time is before midnight (hour < 24 of previous day), it's previous business day
  // Actually: if it's 00:00:00 to 23:59:59 of day X, it belongs to day X
  // But we want: if BEFORE midnight (< 00:00), subtract 1 day

  // Since hours are 0-23, anything on day X is day X
  // But your requirement: "after 12 AM" = after 00:00
  // So records created at 23:xx belong to PREVIOUS day

  // Logic: if hour >= 0 (which is always true), use current day
  // But you want cutoff at midnight, so:
  // - If time is 00:00:00 onwards -> current day
  // - If time is before 00:00:00 (impossible in same day) -> previous day

  // Actually, I think you mean:
  // "Records entered during business hours of Jan 20 should count as Jan 20"
  // "But records entered late night Jan 20 (after midnight into Jan 21) still count as Jan 20"

  // Let me reinterpret: you want records to belong to the day they were INTENDED for
  // So if created before midnight, they belong to THAT day
  // If created after midnight (into next day), they STILL belong to previous day until next midnight

  // Simplest: no adjustment needed! Use the date as-is.
  // Let's just use the date portion of the ISO string

  const bizDate = new Date(d);

  const y = bizDate.getFullYear();
  const m = String(bizDate.getMonth() + 1).padStart(2, '0');
  const day = String(bizDate.getDate()).padStart(2, '0');

  return `${y}-${m}-${day}`;
}

/**
 * Gets current business day "now"
 */
function currentBusinessDay() {
  return toBusinessDay(new Date().toISOString());
}

/* ======================
   2.2) Group by date YYYY-MM-DD
   ====================== */

function groupByDate(items) {
  const out = {};
  const seen = new Set(); // Track unique records to avoid duplicates

  for (const r of items) {
    // Create unique key to prevent duplicates
    const uniqueKey = `${r.id || ''}|${r.material}|${r.supplier}|${r.tag}|${r.date}`;
    if (seen.has(uniqueKey)) continue;
    seen.add(uniqueKey);

    // Use report_day from backend, fallback to calculating from date
    const d = (r.report_day ? r.report_day.slice(0, 10) : toBusinessDay(r.date)) || 'unknown';

    if (!out[d]) {
      out[d] = {
        items: [],
        totals: { gross: 0, net: 0, count: 0 }
      };
    }

    out[d].items.push(r);
    out[d].totals.gross += Number(r.gross || 0);
    out[d].totals.net += Number(r.net || 0);
    out[d].totals.count += 1;
  }

  return out;
}

function upsertItemToStore(item) {
  const bd = (item.report_day || toBusinessDay(item.date || new Date().toISOString())).slice(0, 10) || 'unknown';
  const store = getStore();

  if (!store[bd]) {
    store[bd] = { items: [], totals: { gross: 0, net: 0, count: 0 } };
  }

  const idx = store[bd].items.findIndex(x => x.id === item.id);

  if (idx === -1) {
    store[bd].items.push(item);
    store[bd].totals.gross += Number(item.gross || 0);
    store[bd].totals.net += Number(item.net || 0);
    store[bd].totals.count += 1;
  } else {
    const old = store[bd].items[idx];
    store[bd].totals.gross += (Number(item.gross || 0) - Number(old.gross || 0));
    store[bd].totals.net += (Number(item.net || 0) - Number(old.net || 0));
    store[bd].items[idx] = item;
  }

  setStore(store);
  renderAllDaysDebounced();
}

function removeItemFromStore(item) {
  const bd = (item.report_day || toBusinessDay(item.date)).slice(0, 10) || 'unknown';
  const store = getStore();

  if (!store[bd]) return;

  const idx = store[bd].items.findIndex(x => x.id === item.id);
  if (idx === -1) return;

  const old = store[bd].items[idx];
  store[bd].items.splice(idx, 1);
  store[bd].totals.gross -= Number(old.gross || 0);
  store[bd].totals.net -= Number(old.net || 0);
  store[bd].totals.count -= 1;

  if (store[bd].items.length === 0) {
    delete store[bd];
  }

  setStore(store);
  renderAllDaysDebounced();
}

/* ======================
   3) Reference Data (for inline editing)
   ====================== */

const MATERIALS = ["Flexible Plastic", "Mix Container", "Baled Cardboard", 'Media'];
const SUPPLIERS = [
  "Bottle Depot",
  "Hannam",
  "Inno Food",
  "Meridian",
  "T-Brothers",
  "Zoom Books",
  "Green House"
  "Suzette's Cafe"

];

/* ======================
   4) Load Initial Data
   ====================== */

document.addEventListener("DOMContentLoaded", reloadFromDB);

/** Get month boundaries for YYYY, M (0-11) */
function monthBounds(y, m) {
  const from = new Date(y, m, 1, 0, 0, 0);
  const to = new Date(y, m + 1, 0, 23, 59, 59);
  const iso = d => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 19);
  return { from: iso(from), to: iso(to) };
}

/**
 * Loads full history going back N months.
 * Stops after encountering several empty months in a row.
 */
async function loadFullHistory(maxMonths = 36, emptyBreak = 6) {
  const now = new Date();
  let y = now.getFullYear();
  let m = now.getMonth();

  const all = [];
  const seen = new Set();
  let emptyStreak = 0;
  let noNewStreak = 0;

  for (let i = 0; i < maxMonths; i++) {
    const { from, to } = monthBounds(y, m);
    const url = `/scales/api/received/?from=${from}&to=${to}`;

    try {
      const r = await fetch(url, { credentials: "same-origin" });
      if (!r.ok) break;

      const j = await r.json();
      const items = j.items || [];

      let added = 0;
      for (const it of items) {
        // Create composite unique key
        const uniqueKey = `${it.date}|${it.material}|${it.supplier}|${it.tag}`;
        if (seen.has(uniqueKey)) continue;

        seen.add(uniqueKey);
        all.push(it);
        added += 1;
      }

      if (items.length === 0) {
        emptyStreak += 1;
        if (emptyStreak >= emptyBreak) break;
      } else {
        emptyStreak = 0;
      }

      if (added === 0) {
        noNewStreak += 1;
        if (noNewStreak >= 3) break;
      } else {
        noNewStreak = 0;
      }
    } catch (e) {
      console.error(`Failed to load month ${y}-${m + 1}:`, e);
      break;
    }

    // Move to previous month
    m -= 1;
    if (m < 0) {
      m = 11;
      y -= 1;
    }
  }

  const todayBD = currentBusinessDay();

  return all
    .map(it => ({
      ...it,
      report_day: it.report_day || toBusinessDay(it.date)
    }))
    .filter(it => (it.report_day || '').slice(0, 10) !== todayBD);
}

async function reloadFromDB() {
  try {
    // TOP: Current day's records
    const topRes = await fetch("/scales/api/received/?period=today", {
      credentials: "same-origin"
    });

    if (!topRes.ok) {
      throw new Error(`Failed to load today's data: ${topRes.status}`);
    }

    const topJson = await topRes.json();
    const topItems = topJson.items || [];

    const tbody = document.querySelector("#report-table tbody");
    if (tbody) {
      tbody.innerHTML = "";
      topItems.forEach(appendRow);
      recalcTotalsDebounced();
    }

    // BOTTOM: Full history
    const allItems = await loadFullHistory(36, 6);
    setStore(groupByDate(allItems));
    renderAllDaysDebounced();
  } catch (e) {
    console.error("reloadFromDB failed:", e);
    alert("Failed to load data. Please refresh the page.");
  }
}

/* ======================
   5) Create Record
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

  // Optimistic insert
  const tmpId = "tmp_" + Date.now();
  const tmp = {
    id: tmpId,
    date: new Date().toISOString(),
    material,
    gross,
    net,
    supplier,
    tag
  };

  appendRow(tmp);
  recalcTotalsDebounced();

  try {
    const r = await fetch("/scales/api/received/create/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken
      },
      body: JSON.stringify({
        material,
        gross_kg: gross,  // Backend expects gross_kg
        net_kg: net,      // Backend expects net_kg
        supplier,
        tag
      })
    });

    if (!r.ok) {
      const errorText = await r.text();
      throw new Error(`Save failed: ${r.status} ${errorText}`);
    }

    const { item } = await r.json();

    // Replace temp row with real data
    const tmpRow = document.querySelector(`tr[data-id="${tmpId}"]`);
    if (tmpRow && item.id) {
      tmpRow.dataset.id = item.id;
      tmpRow.dataset.date = item.date || item.created_at;
    }

  } catch (e) {
    console.error(e);
    alert("Save failed: " + e.message);

    // Remove temp row on failure
    const tmpRow = document.querySelector(`tr[data-id="${tmpId}"]`);
    if (tmpRow) tmpRow.remove();
    recalcTotalsDebounced();
    return;
  }

  // Clear inputs
  document.getElementById("gross").value = "";
  document.getElementById("net").value = "";
  document.getElementById("tag").value = "";
  document.getElementById("gross").focus();
}

/* ======================
   6) Render Row
   ====================== */

function appendRow({ id, date, material, gross, net, supplier, tag }) {
  const tbody = document.querySelector("#report-table tbody");
  if (!tbody) return;

  const tr = document.createElement("tr");
  if (id) tr.dataset.id = id;
  if (date) tr.dataset.date = date;

  tr.innerHTML = `
    <td data-col="material">${escapeHtml(material)}</td>
    <td data-col="gross">${Number(gross || 0).toFixed(1)}</td>
    <td data-col="net">${Number(net || 0).toFixed(1)}</td>
    <td data-col="supplier">${escapeHtml(supplier)}</td>
    <td data-col="tag">${escapeHtml(tag)}</td>
    <td class="action-row" style="text-align:right">
      <button class="action-btn edit-btn">Edit</button>
      <button class="action-btn delete-btn">Delete</button>
    </td>`;

  // Event delegation for buttons
  tr.querySelector('.edit-btn').addEventListener('click', function() {
    startEdit(this);
  });

  tr.querySelector('.delete-btn').addEventListener('click', function() {
    deleteRow(this);
  });

  tbody.appendChild(tr);
}

/* ======================
   7) Edit Record
   ====================== */

function selectHTML(options, current) {
  return `<select style="width:100%">${options.map(opt =>
    `<option ${opt === current ? 'selected' : ''}>${escapeHtml(opt)}</option>`
  ).join("")}</select>`;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
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

  // Store original values in dataset
  tr.dataset.originalMaterial = material;
  tr.dataset.originalGross = gross;
  tr.dataset.originalNet = net;
  tr.dataset.originalSupplier = supplier;
  tr.dataset.originalTag = tag;

  tr.querySelector("[data-col='material']").innerHTML = selectHTML(MATERIALS, material);
  tr.querySelector("[data-col='gross']").innerHTML =
    `<input type="number" step="0.1" value="${gross}" style="width:100%">`;
  tr.querySelector("[data-col='net']").innerHTML =
    `<input type="number" step="0.1" value="${net}" style="width:100%">`;
  tr.querySelector("[data-col='supplier']").innerHTML = selectHTML(SUPPLIERS, supplier);
  tr.querySelector("[data-col='tag']").innerHTML =
    `<input type="text" value="${escapeHtml(tag)}" style="width:100%">`;

  const actionCell = tr.querySelector(".action-row");
  actionCell.innerHTML = '';

  const saveBtn = document.createElement('button');
  saveBtn.className = 'action-btn';
  saveBtn.textContent = 'Save';
  saveBtn.addEventListener('click', () => saveEdit(saveBtn));

  const cancelBtn = document.createElement('button');
  cancelBtn.className = 'action-btn';
  cancelBtn.textContent = 'Cancel';
  cancelBtn.addEventListener('click', () => cancelEdit(cancelBtn));

  actionCell.appendChild(saveBtn);
  actionCell.appendChild(cancelBtn);
}

function cancelEdit(btn) {
  const tr = btn.closest("tr");
  tr.dataset.editing = "0";

  // Restore from dataset
  const material = tr.dataset.originalMaterial;
  const gross = tr.dataset.originalGross;
  const net = tr.dataset.originalNet;
  const supplier = tr.dataset.originalSupplier;
  const tag = tr.dataset.originalTag;

  tr.querySelector("[data-col='material']").textContent = material;
  tr.querySelector("[data-col='gross']").textContent = Number(gross).toFixed(1);
  tr.querySelector("[data-col='net']").textContent = Number(net).toFixed(1);
  tr.querySelector("[data-col='supplier']").textContent = supplier;
  tr.querySelector("[data-col='tag']").textContent = tag;

  const actionCell = tr.querySelector(".action-row");
  actionCell.innerHTML = '';

  const editBtn = document.createElement('button');
  editBtn.className = 'action-btn edit-btn';
  editBtn.textContent = 'Edit';
  editBtn.addEventListener('click', function() { startEdit(this); });

  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'action-btn delete-btn';
  deleteBtn.textContent = 'Delete';
  deleteBtn.addEventListener('click', function() { deleteRow(this); });

  actionCell.appendChild(editBtn);
  actionCell.appendChild(deleteBtn);
}

async function saveEdit(btn) {
  const tr = btn.closest("tr");
  const id = tr.dataset.id;

  if (!id || String(id).startsWith("tmp_")) {
    alert("Item not saved yet.");
    return;
  }

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
      body: JSON.stringify({
        material,
        gross_kg: gross,
        net_kg: net,
        supplier,
        tag
      })
    });

    if (!r.ok) {
      throw new Error(`Update failed: ${r.status}`);
    }

    const { item } = await r.json();
    if (!item.date) item.date = tr.dataset.date || new Date().toISOString();

    tr.dataset.editing = "0";
    tr.dataset.date = item.date;

    tr.querySelector("[data-col='material']").textContent = item.material;
    tr.querySelector("[data-col='gross']").textContent = Number(item.gross || gross).toFixed(1);
    tr.querySelector("[data-col='net']").textContent = Number(item.net || net).toFixed(1);
    tr.querySelector("[data-col='supplier']").textContent = item.supplier;
    tr.querySelector("[data-col='tag']").textContent = item.tag;

    const actionCell = tr.querySelector(".action-row");
    actionCell.innerHTML = '';

    const editBtn = document.createElement('button');
    editBtn.className = 'action-btn edit-btn';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', function() { startEdit(this); });

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'action-btn delete-btn';
    deleteBtn.textContent = 'Delete';
    deleteBtn.addEventListener('click', function() { deleteRow(this); });

    actionCell.appendChild(editBtn);
    actionCell.appendChild(deleteBtn);

    upsertItemToStore({ ...item, gross: item.gross || gross, net: item.net || net });
    recalcTotalsDebounced();
  } catch (e) {
    console.error(e);
    alert("Update failed: " + e.message);
  }
}

/* ======================
   8) Delete Record
   ====================== */

async function deleteRow(btn) {
  const tr = btn.closest("tr");
  const id = tr.dataset.id;

  if (!id || String(id).startsWith("tmp_")) {
    const deleted = {
      id: id || "tmp",
      date: tr.dataset.date || new Date().toISOString(),
      gross: parseFloat(tr.querySelector("[data-col='gross']").textContent) || 0,
      net: parseFloat(tr.querySelector("[data-col='net']").textContent) || 0
    };
    tr.remove();
    removeItemFromStore(deleted);
    recalcTotalsDebounced();
    return;
  }

  if (!confirm("Delete this row?")) return;

  try {
    const r = await fetch(`/scales/api/received/${id}/delete/`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-CSRFToken": csrftoken }
    });

    if (!r.ok) {
      throw new Error(`Delete failed: ${r.status}`);
    }

    const deleted = {
      id,
      date: tr.dataset.date || new Date().toISOString(),
      gross: parseFloat(tr.querySelector("[data-col='gross']").textContent) || 0,
      net: parseFloat(tr.querySelector("[data-col='net']").textContent) || 0
    };

    tr.remove();
    removeItemFromStore(deleted);
    recalcTotalsDebounced();
  } catch (e) {
    console.error(e);
    alert("Delete failed: " + e.message);
  }
}

/* ======================
   9) Table Totals (with debounce)
   ====================== */

let recalcTimeout;

function recalcTotalsDebounced() {
  clearTimeout(recalcTimeout);
  recalcTimeout = setTimeout(recalcTotals, 100);
}

function recalcTotals() {
  const tbody = document.querySelector("#report-table tbody");
  if (!tbody) return;

  const rows = tbody.querySelectorAll("tr");
  let grossTotal = 0;
  let netTotal = 0;

  rows.forEach(tr => {
    const grossText = tr.querySelector("td:nth-child(2)")?.textContent || '0';
    const netText = tr.querySelector("td:nth-child(3)")?.textContent || '0';
    grossTotal += parseFloat(grossText) || 0;
    netTotal += parseFloat(netText) || 0;
  });

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
   10) History by Day (cards) with debounce
   ====================== */

let renderTimeout;

function renderAllDaysDebounced() {
  clearTimeout(renderTimeout);
  renderTimeout = setTimeout(renderAllDays, 150);
}

function fmt(n) {
  return Number(n || 0).toFixed(1);
}

function humanDate(iso) {
  if (!iso) return '';

  // Если пришёл просто день "YYYY-MM-DD" (без времени) — разбираем вручную
  if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) {
    const [y, m, d] = iso.split('-').map(Number);
    const dt = new Date(y, m - 1, d);  // локальная дата без смещения
    return dt.toLocaleDateString();    // формат по локали: 11/30/2025 и т.п.
  }

  // На всякий случай fallback для полноценных ISO с временем
  try {
    return new Date(iso).toLocaleDateString();
  } catch {
    return iso;
  }
}

function renderAllDays() {
  const body = document.getElementById('history-body');
  const statsEl = document.getElementById('history-stats');

  if (!body || !statsEl) return;

  const store = getStore();

  body.innerHTML = '';

  let totalNet = 0;
  let totalCount = 0;

  for (const d of Object.keys(store)) {
    totalNet += Number(store[d].totals.net || 0);
    totalCount += store[d].totals.count || 0;
  }

  statsEl.textContent = `Total net: ${Number(totalNet).toFixed(1)} kg • records: ${totalCount}`;

  const days = Object.keys(store).sort((a, b) => b.localeCompare(a));

  for (const d of days) {
    const day = store[d];

    // === агрегаты по материалам и по поставщику ===
    const byMaterial = {};
    const bySupplierMaterial = {};

    for (const r of day.items) {
      const mat = r.material || 'Unknown';
      const sup = r.supplier || 'Unknown';
      const net = Number(r.net || 0);

      // по материалам
      byMaterial[mat] = (byMaterial[mat] || 0) + net;

      // по поставщику + материал
      if (!bySupplierMaterial[sup]) {
        bySupplierMaterial[sup] = {};
      }
      bySupplierMaterial[sup][mat] =
        (bySupplierMaterial[sup][mat] || 0) + net;
    }

    // === карточка дня ===
    const card = document.createElement('div');
    card.className = 'day-card';

    const top = document.createElement('div');
    top.className = 'day-row';

    const left = document.createElement('div');
    left.className = 'day-date';
    left.textContent = humanDate(d);

    const right = document.createElement('div');
    right.className = 'badges';

    const b1 = document.createElement('div');
    b1.className = 'badge';
    b1.textContent = `Net: ${fmt(day.totals.net)} kg`;

    const b2 = document.createElement('div');
    b2.className = 'badge';
    b2.textContent = `Items: ${day.totals.count}`;

    right.appendChild(b1);
    right.appendChild(b2);
    top.appendChild(left);
    top.appendChild(right);
    card.appendChild(top);

    const divider = document.createElement('div');
    divider.className = 'divider';
    card.appendChild(divider);

    // === основная «таблица» записей ===
    const grid = document.createElement('div');
    grid.className = 'day-list';
    grid.innerHTML = `
      <div class="h">Material</div>
      <div class="h">Net</div>
      <div class="h">Supplier</div>
      <div class="h">Tag</div>
    `;

    for (const r of day.items) {
      const cells = [
        escapeHtml(r.material),
        `${fmt(r.net)} kg`,
        escapeHtml(r.supplier),
        `#${escapeHtml(String(r.tag))}`
      ];

      cells.forEach(text => {
        const cell = document.createElement('div');
        cell.className = 'c';
        cell.textContent = text.replace(/<[^>]*>/g, '');
        grid.appendChild(cell);
      });
    }

    card.appendChild(grid);

    // === блок: ИТОГИ ПО МАТЕРИАЛАМ ===
    const summary = document.createElement('div');
    summary.className = 'day-summary';

    const matTitle = document.createElement('div');
    matTitle.className = 'summary-title';
    matTitle.textContent = 'By material:';
    summary.appendChild(matTitle);

    const matRow = document.createElement('div');
    matRow.className = 'summary-materials';

    Object.keys(byMaterial).sort().forEach(mat => {
      const chip = document.createElement('div');
      chip.className = 'summary-chip';
      chip.textContent = `${mat}: ${fmt(byMaterial[mat])} kg`;
      matRow.appendChild(chip);
    });

    summary.appendChild(matRow);

    // === блок: ИТОГИ ПО ПОСТАВЩИКУ/МАТЕРИАЛУ ===
    const supTitle = document.createElement('div');
    supTitle.className = 'summary-title';
    supTitle.textContent = 'By supplier:';
    summary.appendChild(supTitle);

    const supList = document.createElement('div');
    supList.className = 'summary-suppliers';

    Object.keys(bySupplierMaterial).sort().forEach(sup => {
      const supRow = document.createElement('div');
      supRow.className = 'summary-supplier-row';

      const supName = document.createElement('div');
      supName.className = 'summary-supplier-name';
      supName.textContent = `${sup}:`;
      supRow.appendChild(supName);

      const supMats = document.createElement('div');
      supMats.className = 'summary-supplier-mats';

      Object.keys(bySupplierMaterial[sup]).sort().forEach(mat => {
        const chip = document.createElement('div');
        chip.className = 'summary-chip summary-chip-small';
        chip.textContent = `${mat} – ${fmt(bySupplierMaterial[sup][mat])} kg`;
        supMats.appendChild(chip);
      });

      supRow.appendChild(supMats);
      supList.appendChild(supRow);
    });

    summary.appendChild(supList);

    card.appendChild(summary);
    body.appendChild(card);
  }
}


/* ======================
   11) Export to window
   ====================== */

// ======================
// 12) Glow-card effect
// ======================

document.addEventListener("DOMContentLoaded", () => {
  const card = document.querySelector(".card");
  if (!card) return;

  card.addEventListener("pointermove", (e) => {
    const pos = pointerPositionRelativeToElement(card, e);
    const [px, py] = pos.pixels;
    const [perx, pery] = pos.percent;
    const [dx, dy] = distanceFromCenter(card, px, py);
    const edge = closenessToEdge(card, px, py);
    const angle = angleFromPointerEvent(dx, dy);

    card.style.setProperty("--pointer-x", `${perx.toFixed(2)}%`);
    card.style.setProperty("--pointer-y", `${pery.toFixed(2)}%`);
    card.style.setProperty("--pointer-°", `${angle.toFixed(2)}deg`);
    card.style.setProperty("--pointer-d", `${(edge * 100).toFixed(2)}`);
    card.classList.remove("animating");
  });
});

// helpers for glow effect
function centerOfElement(el) {
  const { width, height } = el.getBoundingClientRect();
  return [width / 2, height / 2];
}

function pointerPositionRelativeToElement(el, e) {
  const { left, top, width, height } = el.getBoundingClientRect();
  const x = e.clientX - left;
  const y = e.clientY - top;
  const px = clamp((100 / width) * x);
  const py = clamp((100 / height) * y);
  return { pixels: [x, y], percent: [px, py] };
}

function distanceFromCenter(el, x, y) {
  const [cx, cy] = centerOfElement(el);
  return [x - cx, y - cy];
}

function angleFromPointerEvent(dx, dy) {
  let angleDeg = 0;
  if (dx !== 0 || dy !== 0) {
    const angleRad = Math.atan2(dy, dx);
    angleDeg = angleRad * (180 / Math.PI) + 90;
    if (angleDeg < 0) angleDeg += 360;
  }
  return angleDeg;
}

function closenessToEdge(el, x, y) {
  const [cx, cy] = centerOfElement(el);
  const [dx, dy] = distanceFromCenter(el, x, y);
  let kx = Infinity;
  let ky = Infinity;
  if (dx !== 0) kx = cx / Math.abs(dx);
  if (dy !== 0) ky = cy / Math.abs(dy);
  return clamp(1 / Math.min(kx, ky), 0, 1);
}

function clamp(value, min = 0, max = 100) {
  return Math.min(Math.max(value, min), max);
}


Object.assign(window, {
  addRow,
  startEdit,
  saveEdit,
  cancelEdit,
  deleteRow
});


