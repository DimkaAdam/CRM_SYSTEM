/* crm/static/crm/js/export_shipments.js
   Purpose:
   - Open/close "Add Export" sidebar
   - Open/close "View Export" sidebar
   - Load export details via JSON endpoint: /crm/exports/<id>/json/
   - Render documents list (view/download links)
   Notes:
   - This file assumes you already created the Django view:
       path("exports/<int:pk>/json/", views.export_shipment_json, name="export_shipment_json")
   - Create/Update/Delete/Upload endpoints are left as stubs (you can wire them next).
*/

(function () {
  "use strict";

  // ---------------------------
  // Helpers
  // ---------------------------

  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function $all(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split("; ") : [];
    for (let i = 0; i < cookies.length; i++) {
      const parts = cookies[i].split("=");
      const key = decodeURIComponent(parts[0]);
      if (key === name) return decodeURIComponent(parts.slice(1).join("="));
    }
    return null;
  }

  function csrfToken() {
    return getCookie("csrftoken");
  }

  async function fetchJSON(url, options) {
    const res = await fetch(url, options || {});
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`HTTP ${res.status}. ${text}`);
    }
    return res.json();
  }

  function formatISOToLocal(iso) {
    if (!iso) return "—";
    // iso may be date-only or datetime
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return iso;
      // YYYY-MM-DD HH:mm
      const pad = (n) => String(n).padStart(2, "0");
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    } catch (e) {
      return iso;
    }
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = (value === null || value === undefined || value === "") ? "—" : String(value);
  }

  // ---------------------------
  // Elements
  // ---------------------------

  const addBtn = $("#addNewExportBtn");
  const exportFormSidebar = $("#exportFormSidebar");
  const closeExportSidebarBtn = $("#closeExportSidebarBtn");
  const exportForm = $("#exportForm");

  const viewExportSidebar = $("#viewExportSidebar");
  const closeViewExportSidebarBtn = $("#closeViewExportSidebarBtn");

  const editExportBtn = $("#editExportBtn");
  const deleteExportBtn = $("#deleteExportBtn");

  const exportDetailsContent = $("#exportDetailsContent");
  const editExportForm = $("#editExportForm");
  const cancelExportEditBtn = $("#cancelExportEditBtn");

  const openUploadDocBtn = $("#openUploadDocBtn");
  const exportDocsList = $("#exportDocsList");

  // Buttons inside table (created in template)
  const viewButtons = $all(".view-export-btn");
  const uploadButtons = $all(".upload-export-btn");

  // Base path (adjust if your app prefix differs)
  const BASE = "/crm";

  // ---------------------------
  // Sidebar toggles
  // ---------------------------

  function openSidebar(el) {
    if (!el) return;
    el.classList.add("open");
  }

  function closeSidebar(el) {
    if (!el) return;
    el.classList.remove("open");
  }

  function resetViewSidebar() {
    if (exportDocsList) exportDocsList.innerHTML = "";
    if (exportDetailsContent) exportDetailsContent.style.display = "";
    if (editExportForm) editExportForm.style.display = "none";
  }

  // ---------------------------
  // Documents renderer
  // ---------------------------

  function renderDocuments(docs) {
    if (!exportDocsList) return;

    if (!docs || !docs.length) {
      exportDocsList.innerHTML = `<div class="muted" style="padding:10px;">No documents uploaded.</div>`;
      return;
    }

    const rows = docs.map((d) => {
      const safeName = d.file_name || "file";
      const url = d.file_url || "#";
      const typeLabel = d.doc_type_label || d.doc_type || "Document";
      const uploadedAt = d.uploaded_at ? formatISOToLocal(d.uploaded_at) : "—";

      return `
        <div class="doc-row" data-doc-id="${d.id}">
          <div class="doc-main">
            <div class="doc-title">${typeLabel}</div>
            <div class="doc-meta">${safeName} • ${uploadedAt}</div>
          </div>
          <div class="doc-actions">
            <a class="btn btn-sm btn-view" href="${url}" target="_blank" rel="noopener">View</a>
            <a class="btn btn-sm btn-upload" href="${url}" download>Download</a>
          </div>
        </div>
      `;
    }).join("");

    exportDocsList.innerHTML = rows;
  }

  // ---------------------------
  // Load export details
  // ---------------------------

  async function loadExport(exportId) {
    if (!exportId) return;

    resetViewSidebar();
    openSidebar(viewExportSidebar);

    // Optional title placeholder
    setText("exportTitle", `Export #${exportId}`);

    const url = `${BASE}/exports/${exportId}/json/`;
    const data = await fetchJSON(url);

    // Header title
    const titleParts = [];
    if (data.supplier) titleParts.push(data.supplier);
    if (data.grade) titleParts.push(data.grade);
    setText("exportTitle", titleParts.length ? titleParts.join(" • ") : `Export #${data.id}`);

    // Detail fields
    setText("exportDate", data.date || "—");
    setText("exportLane", data.lane || "—");

    setText("exportSupplier", data.supplier || "—");
    setText("exportGrade", data.grade || "—");
    setText("exportCarrier", data.carrier || "—");

    setText("exportHS", data.hs_code || "—");
    setText("exportMode", data.mode_label || data.mode || "—");

    setText("exportBkg", data.bkg_number || "—");
    setText("exportVessel", data.vessel || "—");

    setText("exportDocCO", data.doc_cutoff_at ? formatISOToLocal(data.doc_cutoff_at) : "Not yet out");
    setText("exportERD", data.erd_at ? formatISOToLocal(data.erd_at) : "Not yet out");
    setText("exportCargoCO", data.cargo_cutoff_at ? formatISOToLocal(data.cargo_cutoff_at) : "Not yet out");

    setText("exportStatus", data.status_label || data.status || "—");

    const price = (data.export_price !== null && data.export_price !== undefined) ? data.export_price : "";
    const cur = data.export_currency || "";
    setText("exportPrice", price ? `${price} ${cur}` : "—");

    // Store current id for actions
    if (editExportForm) {
      const hiddenId = $("#editExportId", editExportForm);
      if (hiddenId) hiddenId.value = data.id;
    }
    if (viewExportSidebar) viewExportSidebar.dataset.currentId = String(data.id);

    // Docs
    renderDocuments(data.documents || []);
  }

  // ---------------------------
  // Add Export: open/close + submit (stub)
  // ---------------------------

  if (addBtn) {
    addBtn.addEventListener("click", function () {
      openSidebar(exportFormSidebar);
    });
  }

  if (closeExportSidebarBtn) {
    closeExportSidebarBtn.addEventListener("click", function () {
      closeSidebar(exportFormSidebar);
    });
  }

  if (exportForm) {
    exportForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      // IMPORTANT:
      // Replace this with your actual endpoint, for example:
      // POST /crm/api/exports/  (create)
      // For now we only validate and show clear console output.

      const payload = {
        date: $("#export_date") ? $("#export_date").value : null,
        lane: $("#export_lane") ? $("#export_lane").value : null,
        schedule: $("#export_schedule") ? $("#export_schedule").value : null,
        deal: $("#export_deal") ? $("#export_deal").value : null,
        hs_code: $("#export_hs_code") ? $("#export_hs_code").value : "",
        mode: $("#export_mode") ? $("#export_mode").value : "",
        status: $("#export_status") ? $("#export_status").value : "",
        export_price: $("#export_price") ? $("#export_price").value : null,
        export_currency: $("#export_currency") ? $("#export_currency").value : "USD",
        container_number: $("#export_container") ? $("#export_container").value : "",
        seal_number: $("#export_seal") ? $("#export_seal").value : "",
        etd: $("#export_etd") ? $("#export_etd").value : null,
        eta: $("#export_eta") ? $("#export_eta").value : null,
      };

      console.log("[ExportShipment] create payload:", payload);

      // Example wire-up (when endpoint exists):
      // const created = await fetchJSON(`${BASE}/api/exports/`, {
      //   method: "POST",
      //   headers: {
      //     "Content-Type": "application/json",
      //     "X-CSRFToken": csrfToken(),
      //   },
      //   body: JSON.stringify(payload),
      // });
      // window.location.reload();

      alert("Create endpoint is not wired yet. Payload logged to console.");
    });
  }

  // ---------------------------
  // View Export: button handlers
  // ---------------------------

  viewButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const id = btn.getAttribute("data-id");
      loadExport(id).catch((err) => {
        console.error(err);
        alert("Failed to load export shipment details. See console.");
      });
    });
  });

  // Upload buttons: stub (wire to upload page or modal later)
  uploadButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const id = btn.getAttribute("data-id");
      if (!id) return;

      // Option A: redirect to a dedicated upload page (recommended)
      // window.location.href = `${BASE}/exports/${id}/upload/`;

      // Option B: open view sidebar and then open upload panel
      loadExport(id).then(() => {
        alert("Upload flow is not wired yet. Next step: create /exports/<id>/upload/ endpoint.");
      }).catch((err) => {
        console.error(err);
        alert("Failed to load export shipment. See console.");
      });
    });
  });

  // Row click => open view (optional UX)
  $all(".export-row").forEach((row) => {
    row.addEventListener("dblclick", function () {
      const id = row.getAttribute("data-id");
      loadExport(id).catch((err) => {
        console.error(err);
        alert("Failed to load export shipment details. See console.");
      });
    });
  });

  // Close view sidebar
  if (closeViewExportSidebarBtn) {
    closeViewExportSidebarBtn.addEventListener("click", function () {
      closeSidebar(viewExportSidebar);
      resetViewSidebar();
    });
  }

  // ---------------------------
  // Edit / Delete: stubs
  // ---------------------------

  if (editExportBtn) {
    editExportBtn.addEventListener("click", function () {
      if (!editExportForm || !exportDetailsContent) return;
      exportDetailsContent.style.display = "none";
      editExportForm.style.display = "";
    });
  }

  if (cancelExportEditBtn) {
    cancelExportEditBtn.addEventListener("click", function () {
      if (!editExportForm || !exportDetailsContent) return;
      editExportForm.style.display = "none";
      exportDetailsContent.style.display = "";
    });
  }

  if (editExportForm) {
    editExportForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const currentId = (viewExportSidebar && viewExportSidebar.dataset.currentId) ? viewExportSidebar.dataset.currentId : null;
      if (!currentId) {
        alert("No export selected.");
        return;
      }

      // IMPORTANT:
      // Replace with your update endpoint, for example:
      // PATCH /crm/api/exports/<id>/
      alert("Update endpoint is not wired yet.");
    });
  }

  if (deleteExportBtn) {
    deleteExportBtn.addEventListener("click", async function () {
      const currentId = (viewExportSidebar && viewExportSidebar.dataset.currentId) ? viewExportSidebar.dataset.currentId : null;
      if (!currentId) {
        alert("No export selected.");
        return;
      }

      const ok = confirm(`Delete export #${currentId}?`);
      if (!ok) return;

      // IMPORTANT:
      // Replace with your delete endpoint, for example:
      // DELETE /crm/api/exports/<id>/
      alert("Delete endpoint is not wired yet.");
    });
  }

  // Upload doc button in view sidebar: stub
  if (openUploadDocBtn) {
    openUploadDocBtn.addEventListener("click", function () {
      const currentId = (viewExportSidebar && viewExportSidebar.dataset.currentId) ? viewExportSidebar.dataset.currentId : null;
      if (!currentId) {
        alert("No export selected.");
        return;
      }
      // Recommended: redirect to upload page
      // window.location.href = `${BASE}/exports/${currentId}/upload/`;
      alert("Upload endpoint is not wired yet. Next step: implement /exports/<id>/upload/.");
    });
  }

})();
