
// ===== Helpers =====
function getCookie(name){
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return m ? m.pop() : "";
}
const csrftoken = getCookie('csrftoken');

// ===== Store (JSON в <script id="daily-store">) =====
function getStore(){
  const el = document.getElementById('daily-store');
  try { return JSON.parse(el.textContent || '{}'); } catch { return {}; }
}
function setStore(obj){
  document.getElementById('daily-store').textContent = JSON.stringify(obj);
}
function groupByDate(items){
  const out = {};
  for(const r of items){
    const d = (r.date || '').slice(0,10) || 'unknown';
    if(!out[d]) out[d] = { items: [], totals: {gross:0, net:0, count:0} };
    out[d].items.push(r);
    out[d].totals.gross += +r.gross;
    out[d].totals.net   += +r.net;
    out[d].totals.count += 1;
  }
  return out;
}
function renderAllDays(){
  const root = document.getElementById('daily-sections');
  const store = getStore();
  root.innerHTML = '';
  const days = Object.keys(store).sort((a,b)=> b.localeCompare(a));
  for(const d of days){
    const day = store[d];
    const wrap = document.createElement('div'); wrap.className = 'day-block';
    const head = document.createElement('div'); head.className = 'day-head';
    head.textContent = `${d} — Net: ${day.totals.net.toFixed(1)} kg (${day.totals.count})`;
    const list = document.createElement('ul'); list.className = 'day-list';
    for(const r of day.items){
      const li = document.createElement('li');
      li.textContent = `${r.material} - ${Number(r.net).toFixed(1)} kg — ${r.supplier} — #${r.tag}`;
      list.appendChild(li);
    }
    wrap.appendChild(head); wrap.appendChild(list); root.appendChild(wrap);
  }
}
function upsertItemToStore(item){
  const store = getStore();
  const d = (item.date || '').slice(0,10) || 'unknown';
  if(!store[d]) store[d] = { items: [], totals: {gross:0, net:0, count:0} };
  const idx = store[d].items.findIndex(x=> x.id === item.id);
  if(idx === -1){
    store[d].items.push(item);
    store[d].totals.gross += +item.gross;
    store[d].totals.net   += +item.net;
    store[d].totals.count += 1;
  }else{
    const old = store[d].items[idx];
    store[d].totals.gross += (+item.gross - +old.gross);
    store[d].totals.net   += (+item.net   - +old.net);
    store[d].items[idx] = item;
  }
  setStore(store); renderAllDays();
}
function removeItemFromStore(item){
  const store = getStore();
  const d = (item.date || '').slice(0,10) || 'unknown';
  if(!store[d]) return;
  const idx = store[d].items.findIndex(x=> x.id === item.id);
  if(idx === -1) return;
  const old = store[d].items[idx];
  store[d].items.splice(idx,1);
  store[d].totals.gross -= +old.gross;
  store[d].totals.net   -= +old.net;
  store[d].totals.count -= 1;
  if(store[d].items.length === 0) delete store[d];
  setStore(store); renderAllDays();
}

// ===== Dictionaries for inline edit =====
const MATERIALS = ["Flexible Plastic","Mix Container","Baled Cardboard"];
const SUPPLIERS = ["Hannam","Inno Food","Meridian","T-Brothers"];

// ===== Initial load =====
document.addEventListener("DOMContentLoaded", reloadFromDB);
async function reloadFromDB(){
  const tbody = document.querySelector("#report-table tbody");
  tbody.innerHTML = "";
  const res = await fetch("/scales/api/received/");
  const {items=[]} = await res.json();
  items.forEach(appendRow);
  recalcTotals();
  setStore(groupByDate(items));
  renderAllDays();
}

// ===== Create =====
async function addRow(){
  const material = document.getElementById("material").value.trim();
  const gross = parseFloat(document.getElementById("gross").value.trim());
  const net = parseFloat(document.getElementById("net").value.trim());
  const supplier = document.getElementById("supplier").value.trim();
  const tag = document.getElementById("tag").value.trim();
  if (!material || isNaN(gross) || isNaN(net) || !supplier || !tag){
    alert("Please fill all fields (weights must be numbers)."); return;
  }

  const tmp = {id:"tmp_"+Date.now(), date:new Date().toISOString(), material, gross, net, supplier, tag};
  appendRow(tmp);
  upsertItemToStore(tmp);          // ← обновим карточки сразу
  recalcTotals();

  try{
    const r = await fetch("/scales/api/received/create/", {
      method:"POST",
      headers: {"Content-Type":"application/json","X-CSRFToken":csrftoken},
      body: JSON.stringify({material, gross, net, supplier, tag})
    });
    if(!r.ok) throw new Error("Save failed");
    await reloadFromDB(); // подтянем реальный id/дату
  }catch(e){
    console.error(e); alert("Save failed. Check server.");
  }

  document.getElementById("gross").value = "";
  document.getElementById("net").value = "";
  document.getElementById("tag").value = "";
  document.getElementById("gross").focus();
}


// ===== Table row render =====
function appendRow({id, date, material, gross, net, supplier, tag}){
  const tbody = document.querySelector("#report-table tbody");
  const tr = document.createElement("tr");
  if(id) tr.dataset.id = id;
  if(date) tr.dataset.date = date;
  tr.innerHTML = `
    <td data-col="material">${material}</td>
    <td data-col="gross">${Number(gross).toFixed(1)}</td>
    <td data-col="net">${Number(net).toFixed(1)}</td>
    <td data-col="supplier">${supplier}</td>
    <td data-col="tag">${tag}</td>
    <td class="action-row">
      <button class="action-btn" onclick="startEdit(this)">Edit</button>
      <button class="action-btn" onclick="deleteRow(this)">Delete</button>
    </td>`;
  tbody.appendChild(tr);
}

// ===== Edit mode =====
function startEdit(btn){
  const tr = btn.closest("tr");
  if(tr.dataset.editing === "1") return;
  tr.dataset.editing = "1";
  const material = tr.querySelector("[data-col='material']").textContent;
  const gross = tr.querySelector("[data-col='gross']").textContent;
  const net = tr.querySelector("[data-col='net']").textContent;
  const supplier = tr.querySelector("[data-col='supplier']").textContent;
  const tag = tr.querySelector("[data-col='tag']").textContent;

  tr.querySelector("[data-col='material']").innerHTML = selectHTML(MATERIALS, material);
  tr.querySelector("[data-col='gross']").innerHTML    = `<input type="number" step="0.1" value="${gross}" style="width:100%">`;
  tr.querySelector("[data-col='net']").innerHTML      = `<input type="number" step="0.1" value="${net}" style="width:100%">`;
  tr.querySelector("[data-col='supplier']").innerHTML = selectHTML(SUPPLIERS, supplier);
  tr.querySelector("[data-col='tag']").innerHTML      = `<input type="text" value="${escapeHtml(tag)}" style="width:100%">`;

  tr.querySelector(".action-row").innerHTML = `
    <button class="action-btn" onclick="saveEdit(this)">Save</button>
    <button class="action-btn" onclick="cancelEdit(this,'${escapeAttr(material)}','${gross}','${net}','${escapeAttr(supplier)}','${escapeAttr(tag)}')">Cancel</button>`;
}
function selectHTML(options, current){
  return `<select style="width:100%">${options.map(opt =>
    `<option ${opt===current?'selected':''}>${opt}</option>`).join("")}</select>`;
}
function escapeHtml(s){ return (s||"").replace(/[&<>"']/g, m=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m])); }
function escapeAttr(s){ return (s||"").replace(/"/g,'&quot;').replace(/'/g,"&#39;"); }
function cancelEdit(btn, material, gross, net, supplier, tag){
  const tr = btn.closest("tr");
  tr.dataset.editing = "0";
  tr.querySelector("[data-col='material']").textContent = material;
  tr.querySelector("[data-col='gross']").textContent = Number(gross).toFixed(1);
  tr.querySelector("[data-col='net']").textContent   = Number(net).toFixed(1);
  tr.querySelector("[data-col='supplier']").textContent = supplier;
  tr.querySelector("[data-col='tag']").textContent = tag;
  tr.querySelector(".action-row").innerHTML = `
    <button class="action-btn" onclick="startEdit(this)">Edit</button>
    <button class="action-btn" onclick="deleteRow(this)">Delete</button>`;
}

async function saveEdit(btn){
  const tr = btn.closest("tr");
  const id = tr.dataset.id;
  if(!id || String(id).startsWith("tmp_")){ alert("Item not saved yet."); return; }

  const material = tr.querySelector("[data-col='material'] select").value.trim();
  const gross = parseFloat(tr.querySelector("[data-col='gross'] input").value.trim());
  const net   = parseFloat(tr.querySelector("[data-col='net'] input").value.trim());
  const supplier = tr.querySelector("[data-col='supplier'] select").value.trim();
  const tag   = tr.querySelector("[data-col='tag'] input").value.trim();
  if(!material || isNaN(gross) || isNaN(net) || !supplier || !tag){ alert("Fill all fields correctly."); return; }

  try{
    const r = await fetch(`/scales/api/received/${id}/update/`, {
      method:"POST",
      headers: {"Content-Type":"application/json","X-CSRFToken":csrftoken},
      body: JSON.stringify({material, gross, net, supplier, tag})
    });
    if(!r.ok) throw new Error("Update failed");
    const { item } = await r.json();
    if(!item.date) item.date = tr.dataset.date || new Date().toISOString();

    // Обновляем DOM
    tr.dataset.editing = "0";
    tr.dataset.date = item.date;
    tr.querySelector("[data-col='material']").textContent = item.material;
    tr.querySelector("[data-col='gross']").textContent    = Number(item.gross).toFixed(1);
    tr.querySelector("[data-col='net']").textContent      = Number(item.net).toFixed(1);
    tr.querySelector("[data-col='supplier']").textContent = item.supplier;
    tr.querySelector("[data-col='tag']").textContent      = item.tag;
    tr.querySelector(".action-row").innerHTML = `
      <button class="action-btn" onclick="startEdit(this)">Edit</button>
      <button class="action-btn" onclick="deleteRow(this)">Delete</button>`;

    // Store + Totals
    upsertItemToStore(item);
    recalcTotals();
  }catch(e){
    console.error(e); alert("Update failed.");
  }
}

// ===== Delete =====
async function deleteRow(btn){
  const tr = btn.closest("tr");
  const id = tr.dataset.id;
  if(!id || String(id).startsWith("tmp_")){ tr.remove(); recalcTotals(); return; }
  if(!confirm("Delete this row?")) return;

  try{
    const r = await fetch(`/scales/api/received/${id}/delete/`, {
      method:"POST",
      headers: {"X-CSRFToken": csrftoken}
    });
    if(!r.ok) throw new Error("Delete failed");

    const deleted = {
      id,
      date: tr.dataset.date || new Date().toISOString(),
      gross: parseFloat(tr.querySelector("[data-col='gross']").textContent) || 0,
      net:   parseFloat(tr.querySelector("[data-col='net']").textContent)   || 0
    };
    tr.remove();
    removeItemFromStore(deleted);
    recalcTotals();
  }catch(e){
    console.error(e); alert("Delete failed.");
  }
}

// ===== Totals =====
function recalcTotals(){
  const grossTotal = [...document.querySelectorAll("#report-table tbody tr td:nth-child(2)")]
    .reduce((s, td) => s + (parseFloat(td.textContent) || 0), 0);
  const netTotal = [...document.querySelectorAll("#report-table tbody tr td:nth-child(3)")]
    .reduce((s, td) => s + (parseFloat(td.textContent) || 0), 0);

  let tfoot = document.querySelector("#report-table tfoot");
  if (!tfoot){
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

function fmt(n){ return Number(n).toFixed(1); }
function humanDate(iso){
  try { return new Date(iso).toLocaleDateString(); } catch { return iso; }
}

function renderAllDays(){
  const body = document.getElementById('history-body');
  const statsEl = document.getElementById('history-stats');
  const store = getStore();
  body.innerHTML = '';

  // small header stats
  let totalNet = 0, totalCount = 0;
  for(const d of Object.keys(store)){
    totalNet += store[d].totals.net;
    totalCount += store[d].totals.count;
  }
  statsEl.textContent = `Total net: ${fmt(totalNet)} kg • records: ${totalCount}`;

  const days = Object.keys(store).sort((a,b)=> b.localeCompare(a));
  for(const d of days){
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
    for(const r of day.items){
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

