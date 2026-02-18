/* crm/static/crm/js/export_shipments.js  (FULL, CLEAN) */

(function () {
  "use strict";

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split("; ") : [];
    for (let i = 0; i < cookies.length; i++) {
      const parts = cookies[i].split("=");
      const key = decodeURIComponent(parts[0].trim());
      if (key === name) return decodeURIComponent(parts.slice(1).join("="));
    }
    return null;
  }

  function csrfToken() { return getCookie("csrftoken"); }

  async function fetchJSON(url, options) {
    const res = await fetch(url, options || {});
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`HTTP ${res.status}. ${text}`);
    }
    return res.json();
  }

  function openSidebar(el) { if (el) el.classList.add("open"); }
  function closeSidebar(el) { if (el) el.classList.remove("open"); }

  function isoToLocalDatetimeValue(iso) {
    if (!iso) return "";
    // 2026-02-03T12:30:00Z or without Z
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return "";
      const pad = (n) => String(n).padStart(2, "0");
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    } catch (e) {
      return "";
    }
  }

  function setValue(el, v) {
    if (!el) return;
    el.value = (v === null || v === undefined) ? "" : String(v);
  }

  const BASE = "/crm";

  // Add sidebar
  const addBtn = $("#addNewExportBtn");
  const exportFormSidebar = $("#exportFormSidebar");
  const closeExportSidebarBtn = $("#closeExportSidebarBtn");
  const exportForm = $("#exportForm");

  // View sidebar
  const viewExportSidebar = $("#viewExportSidebar");
  const closeViewExportSidebarBtn = $("#closeViewExportSidebarBtn");
  const exportTitle = $("#exportTitle");

  // Table
  const viewButtons = $all(".view-export-btn");
  const uploadButtons = $all(".upload-export-btn");
  const inlineFields = $all(".inline-edit");

  // Sidebar details form
  const exportDetailsForm = $("#exportDetailsForm");
  const sidebarExportId = $("#sidebar_export_id");
  const sb_vessel = $("#sb_vessel");
  const sb_hs_code = $("#sb_hs_code");
  const sb_doc_cutoff_at = $("#sb_doc_cutoff_at");
  const sb_erd_at = $("#sb_erd_at");
  const sb_cargo_cutoff_at = $("#sb_cargo_cutoff_at");
  const sb_status = $("#sb_status");
  const sb_export_price = $("#sb_export_price");
  const sb_export_currency = $("#sb_export_currency");
  const sb_container_number = $("#sb_container_number");
  const sb_seal_number = $("#sb_seal_number");
  const sb_etd = $("#sb_etd");
  const sb_eta = $("#sb_eta");
  const sb_notes = $("#sb_notes");
  const sb_save_status = $("#sb_save_status");

  // Documents
  const exportDocsList = $("#exportDocsList");
  const openUploadDocBtn = $("#openUploadDocBtn");
  const uploadInput = $("#exportUploadInput");

  // Delete
  const deleteExportBtn = $("#deleteExportBtn");

  function renderDocuments(docs) {
    if (!exportDocsList) return;

    if (!docs || !docs.length) {
      exportDocsList.innerHTML = '<div class="muted" style="padding:10px;">No documents uploaded.</div>';
      return;
    }

    exportDocsList.innerHTML = docs.map((d) => {
      const safeName = d.file_name || "file";
      const url = d.file_url || "#";
      const typeLabel = d.doc_type_label || d.doc_type || "Document";
      return `
        <div class="doc-row">
          <div class="doc-main">
            <div class="doc-title">${typeLabel}</div>
            <div class="doc-meta">${safeName}</div>
          </div>
          <div class="doc-actions">
            <a class="btn btn-sm btn-view" href="${url}" target="_blank" rel="noopener">View</a>
            <a class="btn btn-sm btn-upload" href="${url}" download>Download</a>
          </div>
        </div>
      `;
    }).join("");
  }

  async function loadExport(exportId) {
    const data = await fetchJSON(`${BASE}/exports/${exportId}/json/`);

    if (viewExportSidebar) viewExportSidebar.dataset.currentId = String(data.id);
    if (sidebarExportId) sidebarExportId.value = String(data.id);

    // Title
    if (exportTitle) {
      const supplier = data.supplier || "";
      const grade = data.grade || "";
      exportTitle.textContent = (supplier || grade) ? `${supplier}${supplier && grade ? " • " : ""}${grade}` : `Export #${data.id}`;
    }

    // Fill sidebar details
    setValue(sb_vessel, data.vessel);
    setValue(sb_hs_code, data.hs_code);

    setValue(sb_doc_cutoff_at, isoToLocalDatetimeValue(data.doc_cutoff_at));
    setValue(sb_erd_at, isoToLocalDatetimeValue(data.erd_at));
    setValue(sb_cargo_cutoff_at, isoToLocalDatetimeValue(data.cargo_cutoff_at));

    setValue(sb_status, data.status);
    setValue(sb_export_price, data.export_price);
    setValue(sb_export_currency, data.export_currency);

    setValue(sb_container_number, data.container_number);
    setValue(sb_seal_number, data.seal_number);

    setValue(sb_etd, data.etd);
    setValue(sb_eta, data.eta);

    setValue(sb_notes, data.notes);

    if (sb_save_status) sb_save_status.textContent = "Loaded";

    renderDocuments(data.documents || []);

    openSidebar(viewExportSidebar);
  }

  // -----------------------
  // Create (Add sidebar)
  // -----------------------
  if (addBtn) addBtn.addEventListener("click", () => openSidebar(exportFormSidebar));
  if (closeExportSidebarBtn) closeExportSidebarBtn.addEventListener("click", () => closeSidebar(exportFormSidebar));

  if (exportForm) {
    exportForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const payload = {
        date: $("#export_date") ? ($("#export_date").value || null) : null,
        lane: $("#export_lane") ? ($("#export_lane").value || null) : null,
        deal_id: $("#export_deal_id") ? ($("#export_deal_id").value || null) : null,
        mode: $("#export_mode") ? $("#export_mode").value : "ocean",
        status: $("#export_status") ? $("#export_status").value : "draft",
        bkg_number: $("#export_bkg_number") ? ($("#export_bkg_number").value || "") : "",
      };

      try {
        const res = await fetchJSON(`${BASE}/api/exports/create/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken(),
          },
          body: JSON.stringify(payload),
        });

        if (res && res.ok === false) {
          alert(res.error || "Create failed");
          return;
        }

        closeSidebar(exportFormSidebar);
        window.location.reload();

      } catch (err) {
        console.error(err);
        alert("Create failed. See console.");
      }
    });
  }

  // -----------------------
  // Inline table edit (short columns)
  // -> POST to update-field (safe, no PATCH issues)
  // -----------------------
  async function saveField(exportId, field, value) {
    return fetchJSON(`${BASE}/api/exports/${exportId}/update-field/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
      },
      body: JSON.stringify({ field, value }),
    });
  }

  inlineFields.forEach((el) => {
    el.addEventListener("change", async function () {
      const exportId = el.getAttribute("data-id");
      const field = el.getAttribute("data-field");
      if (!exportId || !field) return;

      const value = (el.value === "") ? null : el.value;

      el.disabled = true;
      try {
        const res = await saveField(exportId, field, value);
        if (res && res.ok === false) alert(res.error || "Update failed");
      } catch (err) {
        console.error(err);
        alert("Update failed. See console.");
      } finally {
        el.disabled = false;
      }
    });
  });

  // -----------------------
  // Sidebar auto-save (details form)
  // -----------------------
  let sbTimer = null;

  function sidebarCurrentId() {
    return viewExportSidebar?.dataset?.currentId || sidebarExportId?.value || "";
  }

  function sidebarPayload() {
    return {
      vessel: sb_vessel ? sb_vessel.value : "",
      hs_code: sb_hs_code ? sb_hs_code.value : "",

      doc_cutoff_at: sb_doc_cutoff_at ? (sb_doc_cutoff_at.value || null) : null,
      erd_at: sb_erd_at ? (sb_erd_at.value || null) : null,
      cargo_cutoff_at: sb_cargo_cutoff_at ? (sb_cargo_cutoff_at.value || null) : null,

      status: sb_status ? sb_status.value : "",

      export_price: sb_export_price ? (sb_export_price.value || null) : null,
      export_currency: sb_export_currency ? sb_export_currency.value : "USD",

      container_number: sb_container_number ? sb_container_number.value : "",
      seal_number: sb_seal_number ? sb_seal_number.value : "",

      etd: sb_etd ? (sb_etd.value || null) : null,
      eta: sb_eta ? (sb_eta.value || null) : null,

      notes: sb_notes ? sb_notes.value : "",
    };
  }

  async function saveSidebar() {
    const id = sidebarCurrentId();
    if (!id) return;

    if (sb_save_status) sb_save_status.textContent = "Saving...";

    try {
      const res = await fetchJSON(`${BASE}/api/exports/${id}/update/`, {
        method: "POST", // fallback-friendly
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify(sidebarPayload()),
      });

      if (res && res.ok === false) {
        if (sb_save_status) sb_save_status.textContent = res.error || "Save failed";
        return;
      }

      if (sb_save_status) sb_save_status.textContent = "Saved";

    } catch (err) {
      console.error(err);
      if (sb_save_status) sb_save_status.textContent = "Save failed (see console)";
    }
  }

  function scheduleSidebarSave() {
    if (sbTimer) clearTimeout(sbTimer);
    sbTimer = setTimeout(saveSidebar, 400);
  }

  if (exportDetailsForm) {
    exportDetailsForm.addEventListener("input", scheduleSidebarSave);
    exportDetailsForm.addEventListener("change", scheduleSidebarSave);
  }

  // -----------------------
  // View buttons
  // -----------------------
  viewButtons.forEach((btn) => {
    btn.addEventListener("click", async function () {
      const id = btn.getAttribute("data-id");
      if (!id) return;
      try {
        await loadExport(id);
      } catch (err) {
        console.error(err);
        alert("Failed to load export. See console.");
      }
    });
  });

  // Upload buttons (stub UI only)
  uploadButtons.forEach((btn) => {
    btn.addEventListener("click", async function () {
      const id = btn.getAttribute("data-id");
      if (!id) return;
      try {
        await loadExport(id);
        if (openUploadDocBtn) openUploadDocBtn.click();
      } catch (err) {
        console.error(err);
        alert("Failed to open export. See console.");
      }
    });
  });

  if (closeViewExportSidebarBtn) {
    closeViewExportSidebarBtn.addEventListener("click", function () {
      closeSidebar(viewExportSidebar);
      resetViewSidebar();
    });
  }

})();
