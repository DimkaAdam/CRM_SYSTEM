// ===== Префикс для /crm/ =====
function basePrefix() {
  return window.location.pathname.includes("/crm/") ? "/crm/" : "/";
}
function u(p) {
  p = p.startsWith("/") ? p.slice(1) : p;
  return basePrefix() + p;
}

// ===== Helpers =====
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const csrftoken = getCookie("csrftoken");

const byId = (id) => document.getElementById(id);

function toFloat(v, def = 0) {
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : def;
}
function toInt(v, def = 0) {
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? n : def;
}

function assertJSON(response) {
  const ct = response.headers.get("content-type") || "";
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  if (!ct.includes("application/json")) throw new Error(`Not JSON (ct: ${ct})`);
  return response.json();
}
function fetchJSON(url, opts = {}) {
  return fetch(url, opts).then(assertJSON);
}

// ===== Scale Ticket Handlers (GLOBAL) =====
function attachScaleTicketHandlers(root) {
  const scope = root || document;
  const buttons = scope.querySelectorAll(".scale-ticket-status-btn");

  buttons.forEach((btn) => {
    if (btn.dataset.bound === "1") return;
    btn.dataset.bound = "1";

    btn.addEventListener("click", (e) => {
      e.stopPropagation();

      if (btn.classList.contains("sent")) return;

      const path = btn.dataset.path;
      if (!path) {
        alert("No scale ticket file path for this deal.");
        return;
      }

      const oldText = btn.textContent;
      btn.disabled = true;
      btn.textContent = "Sending...";

      fetch(u("send-scale-ticket-email/"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ path }),
      })
        .then(assertJSON)
        .then((data) => {
          if (!data.success) throw new Error(data.error || "Send failed");
          btn.classList.remove("not-sent");
          btn.classList.add("sent");
          btn.textContent = "Sent";
        })
        .catch((err) => {
          console.error("Error sending scale ticket:", err);
          alert("Error sending scale ticket: " + err.message);
          btn.textContent = oldText;
        })
        .finally(() => {
          btn.disabled = false;
        });
    });
  });
}

// ===== Main =====
document.addEventListener("DOMContentLoaded", () => {
  console.log("Scale URL ->", u("api/scale-ticket-counters/"));

  attachScaleTicketHandlers(document);

  // --- Открыть сайдбар "Новая сделка"
  const addNewDealBtn = byId("addNewDealBtn");
  if (addNewDealBtn) {
    addNewDealBtn.addEventListener("click", function () {
      fetchJSON(u("api/scale-ticket-counters/"))
        .then((data) => {
          const input = byId("scale_ticket");
          if (input && data && data.scale_ticket != null) {
            input.value = data.scale_ticket;
          }
        })
        .catch((err) =>
          console.error("Ошибка при получении номера Scale Ticket:", err)
        );

      const sidebar = byId("dealFormSidebar");
      if (sidebar) sidebar.style.width = "400px";
    });
  }

  // --- Закрыть сайдбар "Новая сделка"
  const closeSidebarBtn = byId("closeSidebarBtn");
  if (closeSidebarBtn) {
    closeSidebarBtn.addEventListener("click", function () {
      const sidebar = byId("dealFormSidebar");
      if (sidebar) sidebar.style.width = "0";
    });
  }

  // --- Создать сделку
  const dealForm = byId("dealForm");
  if (dealForm) {
    dealForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const receivedQuantityElement = byId("received_quantity");
      const buyerPriceElement = byId("buyer_price");
      const supplierPriceElement = byId("supplier_price");
      const transportCostElement = byId("transport_cost");

      if (!receivedQuantityElement || !buyerPriceElement || !supplierPriceElement || !transportCostElement) {
        console.error("Элементы формы не найдены!");
        return;
      }

      const received_quantity = toFloat(receivedQuantityElement.value);
      const buyer_price = toFloat(buyerPriceElement.value);
      const supplier_price = toFloat(supplierPriceElement.value);
      const transport_cost = toFloat(transportCostElement.value);
      const shipped_quantity = toFloat(byId("shipped_quantity")?.value);

      const data = {
        date: byId("date")?.value,
        supplier: toInt(byId("supplier")?.value),
        buyer: toInt(byId("buyer")?.value),
        grade: byId("grade")?.value,
        shipped_quantity,
        shipped_pallets: toInt(byId("shipped_pallets")?.value),
        received_quantity,
        received_pallets: toInt(byId("received_pallets")?.value),
        supplier_price,
        buyer_price,
        transport_cost,
        transport_company: toInt(byId("transport_company")?.value),
        scale_ticket: byId("scale_ticket")?.value,
      };

      fetchJSON(u("api/deals/"), {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
        body: JSON.stringify(data),
      })
        .then((dealData) => {
          console.log("Deal created:", dealData);

          const tbody = byId("dealTable")?.getElementsByTagName("tbody")?.[0];
          if (tbody) {
            const tr = tbody.insertRow();
            tr.classList.add("deal-row");
            tr.dataset.id = dealData.id ?? "";
            tr.innerHTML = `
              <td>${dealData.date ?? ""}</td>
              <td>${dealData.supplier_name ?? ""}</td>
              <td>${dealData.buyer ?? ""}</td>
              <td>${dealData.grade ?? ""}</td>
              <td>${dealData.shipped_quantity ?? ""} / ${dealData.shipped_pallets ?? ""}</td>
              <td>${dealData.received_quantity ?? ""} / ${dealData.received_pallets ?? ""}</td>
              <td>${dealData.supplier_price ?? ""}</td>
              <td>${dealData.supplier_total ?? ""}</td>
              <td>${dealData.buyer_price ?? ""}</td>
              <td>${dealData.total_amount ?? ""}</td>
              <td>${dealData.transport_cost ?? ""}</td>
              <td>${dealData.transport_company?.name ?? dealData.transport_company ?? ""}</td>
              <td>${dealData.scale_ticket ?? "N/A"}</td>
              <td>${dealData.total_income_loss ?? ""}</td>
              <td>
                ${dealData.scale_ticket
                  ? `<button class="scale-ticket-status-btn ${dealData.scale_ticket_sent ? "sent" : "not-sent"}"
                             data-path="${dealData.scale_ticket_relative_path || ""}">
                       ${dealData.scale_ticket_sent ? "Sent" : "Send"}
                     </button>`
                  : `<span class="no-scale-ticket">N/A</span>`}
              </td>
            `;
            attachDealRowHandler(tr);
            attachScaleTicketHandlers(tr);
          }

          const sidebar = byId("dealFormSidebar");
          if (sidebar) sidebar.style.width = "0";
          dealForm.reset();

          return fetch(u("api/scale-ticket-counters/increment/"), {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
          });
        })
        .then((response) => {
          if (response && response.ok) {
            console.log("✅ Scale ticket counter incremented");
            return response.json();
          } else if (response) {
            console.error("❌ Failed to increment counter:", response.status);
          }
        })
        .then((counterData) => {
          if (counterData) console.log("New counter value:", counterData);
        })
        .catch((err) => {
          console.error("Error (create deal or increment):", err);
          alert("Ошибка: " + err.message);
        });
    });
  }

  // --- Открыть сайдбар деталей по клику на строку
  function attachDealRowHandler(row) {
    row.addEventListener("click", (e) => {
      if (e.target.closest(".scale-ticket-status-btn")) return;

      const dealId = row.dataset.id;
      if (!dealId) return;

      fetchJSON(u(`deals/${dealId}/`))
        .then((data) => {
          // ── Базовые поля ──────────────────────────────────────────
          byId("dealDate")        && (byId("dealDate").innerText        = data.date          ?? "");
          byId("dealSupplier")    && (byId("dealSupplier").innerText    = data.supplier_name ?? "");
          byId("dealBuyer")       && (byId("dealBuyer").innerText       = data.buyer_name    ?? "");
          byId("dealGrade")       && (byId("dealGrade").innerText       = data.grade         ?? "");
          byId("dealTotalAmount") && (byId("dealTotalAmount").innerText = data.total_amount  ?? "");
          byId("dealScaleTicket") && (byId("dealScaleTicket").innerText = data.scale_ticket  ?? "");

          // ── ВОТ СЮДА: заменяем весь старый KPI-блок одним вызовом ──
          renderDealAnalytics({
            profit:          toFloat(data.total_income_loss),
            profitPerTon:    toFloat(data.profit_per_ton),
            spreadPerTon:    toFloat(data.spread_per_ton),
            transportPerTon: toFloat(data.transport_per_ton),
            transportShare:  toFloat(data.transport_share),
            variance:        toFloat(data.variance_mt),
            avgPalletWeight: toFloat(data.avg_pallet_weight_kg),
          });
          // ──────────────────────────────────────────────────────────

          const sidebar = byId("viewDealSidebar");
          if (sidebar) {
            sidebar.dataset.dealId = dealId;
            sidebar.style.width = "400px";
          }
        })
        .catch((err) => console.error("Error fetching deal details:", err));
    });
  }

  document.querySelectorAll(".deal-row").forEach(attachDealRowHandler);

  // --- Закрыть сайдбар деталей
  const closeViewDealSidebarBtn = byId("closeViewDealSidebarBtn");
  if (closeViewDealSidebarBtn) {
    closeViewDealSidebarBtn.addEventListener("click", () => {
      const sidebar = byId("viewDealSidebar");
      if (sidebar) sidebar.style.width = "0";
    });
  }

  // Glass panel config
  const glassProps = {
    displace: 15, distortionScale: -150,
    redOffset: 5, greenOffset: 15, blueOffset: 25,
    brightness: 0.60, opacity: 0.80, mixBlendMode: "screen",
  };

  function applyGlassProps(el, props) {
    if (!el) return;
    el.style.setProperty("--rgb-r",        `${props.redOffset   || 0}px`);
    el.style.setProperty("--rgb-g",        `${props.greenOffset || 0}px`);
    el.style.setProperty("--rgb-b",        `${props.blueOffset  || 0}px`);
    el.style.setProperty("--brightness",   String(props.brightness ?? 1));
    el.style.setProperty("--glass-opacity",String(props.opacity  ?? 0.85));
    el.style.setProperty("--mix",           props.mixBlendMode || "screen");

    const filter = document.querySelector("#glass-disp");
    const turb   = filter?.querySelector("feTurbulence");
    const disp   = filter?.querySelector("feDisplacementMap");

    if (turb) {
      const base = 0.004 + Math.min(Math.max((props.displace || 0) / 100, 0), 0.12);
      turb.setAttribute("baseFrequency", base.toFixed(4));
    }
    if (disp) disp.setAttribute("scale", String(Math.abs(props.distortionScale ?? 10)));
  }

  const glass = document.querySelector("#viewDealSidebar .glass-panel");
  applyGlassProps(glass, glassProps);

  // --- Включить режим редактирования
  const editDealBtn = byId("editDealBtn");
  if (editDealBtn) {
    editDealBtn.addEventListener("click", () => {
      const sidebar = byId("viewDealSidebar");
      sidebar && sidebar.classList.add("editing");
      byId("dealDetailsContent") && (byId("dealDetailsContent").style.display = "none");
      byId("editDealForm")       && (byId("editDealForm").style.display       = "block");

      const dealId = byId("viewDealSidebar")?.dataset.dealId;
      if (!dealId) return;

      fetchJSON(u(`deals/${dealId}/`))
        .then((data) => {
          byId("editDate")             && (byId("editDate").value             = data.date               ?? "");
          byId("editSupplier")         && (byId("editSupplier").value         = data.supplier_id         ?? "");
          byId("editBuyer")            && (byId("editBuyer").value            = data.buyer_id            ?? "");
          byId("editGrade")            && (byId("editGrade").value            = data.grade               ?? "");
          byId("editShippedQuantity")  && (byId("editShippedQuantity").value  = data.shipped_quantity    ?? "");
          byId("editShippedPallets")   && (byId("editShippedPallets").value   = data.shipped_pallets     ?? "");
          byId("editReceivedQuantity") && (byId("editReceivedQuantity").value = data.received_quantity   ?? "");
          byId("editReceivedPallets")  && (byId("editReceivedPallets").value  = data.received_pallets    ?? "");
          byId("editSupplierPrice")    && (byId("editSupplierPrice").value    = data.supplier_price      ?? "");
          byId("editBuyerPrice")       && (byId("editBuyerPrice").value       = data.buyer_price         ?? "");
          byId("editTransportCost")    && (byId("editTransportCost").value    = data.transport_cost      ?? "");
          byId("editTransportCompany") && (byId("editTransportCompany").value = data.transport_company_id?? "");
          byId("editScaleTicket")      && (byId("editScaleTicket").value      = data.scale_ticket        ?? "");
        })
        .catch((err) => console.error("Error fetching data for editing:", err));
    });
  }

  // --- Отмена редактирования
  const cancelEditBtn = byId("cancelEditBtn");
  if (cancelEditBtn) {
    cancelEditBtn.addEventListener("click", () => {
      const sidebar = byId("viewDealSidebar");
      sidebar && sidebar.classList.remove("editing");
      byId("dealDetailsContent") && (byId("dealDetailsContent").style.display = "block");
      byId("editDealForm")       && (byId("editDealForm").style.display       = "none");
    });
  }

  // --- Сохранить изменения
  const editDealForm = byId("editDealForm");
  if (editDealForm) {
    editDealForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const dealId = byId("viewDealSidebar")?.dataset.dealId;
      if (!dealId) return;

      const payload = {
        date:              byId("editDate")?.value,
        supplier:          toInt(byId("editSupplier")?.value),
        buyer:             toInt(byId("editBuyer")?.value),
        grade:             byId("editGrade")?.value,
        shipped_quantity:  toFloat(byId("editShippedQuantity")?.value),
        shipped_pallets:   toInt(byId("editShippedPallets")?.value),
        received_quantity: toFloat(byId("editReceivedQuantity")?.value),
        received_pallets:  toInt(byId("editReceivedPallets")?.value),
        supplier_price:    toFloat(byId("editSupplierPrice")?.value),
        buyer_price:       toFloat(byId("editBuyerPrice")?.value),
        transport_cost:    toFloat(byId("editTransportCost")?.value),
        transport_company: toInt(byId("editTransportCompany")?.value),
        scale_ticket:      byId("editScaleTicket")?.value,
      };

      fetchJSON(u(`deals/${dealId}/edit/`), {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
        body: JSON.stringify(payload),
      })
        .then((data) => {
          byId("viewDealSidebar")?.classList.remove("editing");
          alert("Changes saved successfully!");
          byId("dealDate")        && (byId("dealDate").innerText        = data.date         ?? "");
          byId("dealSupplier")    && (byId("dealSupplier").innerText    = data.supplier      ?? "");
          byId("dealBuyer")       && (byId("dealBuyer").innerText       = data.buyer         ?? "");
          byId("dealGrade")       && (byId("dealGrade").innerText       = data.grade         ?? "");
          byId("dealTotalAmount") && (byId("dealTotalAmount").innerText = data.total_amount  ?? "");
          byId("dealDetailsContent") && (byId("dealDetailsContent").style.display = "block");
          byId("editDealForm")       && (byId("editDealForm").style.display       = "none");
        })
        .catch((err) => console.error("Error saving changes:", err));
    });
  }

  // --- Удаление сделки
  const deleteDealBtn = byId("deleteDealBtn");
  if (deleteDealBtn) {
    deleteDealBtn.addEventListener("click", () => {
      const dealId = byId("viewDealSidebar")?.dataset.dealId;
      if (!dealId) return;

      if (confirm("Are you sure you want to delete this deal?")) {
        fetch(u(`deals/${dealId}/delete/`), {
          method: "DELETE",
          headers: { "X-CSRFToken": csrftoken },
        })
          .then((r) => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            alert("Deal deleted successfully!");
            byId("viewDealSidebar") && (byId("viewDealSidebar").style.width = "0");
            document.querySelector(`.deal-row[data-id="${dealId}"]`)?.remove();
          })
          .catch((err) => console.error("Error deleting deal:", err));
      }
    });
  }

  // ===== Scale ticket sidebar =====
  window.openScaleTicketSidebarFromDeal = function () {
    const scaleTicket = byId("dealScaleTicket")?.innerText;
    if (!scaleTicket || scaleTicket === "N/A") {
      alert("⛔ Опа, нема номера Scale Ticket.");
      return;
    }
    openScaleTicketSidebar();
    setTimeout(() => {
      const input = byId("ticket_number");
      if (input) { input.value = scaleTicket; fetchDealData(); }
    }, 300);
  };

  (function initScaleTicketSidebar() {
    const sidebar = byId("scaleTicketSidebar");
    if (!sidebar) return;

    window.openScaleTicketSidebar = function () {
      sidebar.style.display = "block";
      setTimeout(() => sidebar.classList.add("open"), 10);
    };
    window.closeScaleTicketSidebar = function () {
      sidebar.classList.remove("open");
      setTimeout(() => (sidebar.style.display = "none"), 300);
    };

    const closeBtn = document.querySelector("#scaleTicketSidebar .close-btn");
    closeBtn && closeBtn.addEventListener("click", closeScaleTicketSidebar);
  })();

  const generateMonthBtn = byId("generateMonthScaleTicketsBtn");

  if (generateMonthBtn) {
    generateMonthBtn.addEventListener("click", async function () {
      try {
        generateMonthBtn.disabled = true;

        const params = new URLSearchParams(window.location.search);
        const month = params.get("month");
        const year = params.get("year");

        const response = await fetch(u("generate-current-month-scale-tickets-archive/"), {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
          },
          body: JSON.stringify({
            month: month,
            year: year
          })
        });

        const contentType = response.headers.get("content-type") || "";

        if (!response.ok) {
          const text = await response.text();
          throw new Error(`HTTP ${response.status}: ${text.slice(0, 200)}`);
        }

        if (!contentType.includes("application/json")) {
          const text = await response.text();
          throw new Error(`Server returned non-JSON response: ${text.slice(0, 200)}`);
        }

        const data = await response.json();

        if (!data.success) {
          throw new Error(data.error || "Failed to generate archive");
        }

        let msg = `Done for ${data.month}/${data.year}\nCreated: ${data.created}\nSkipped: ${data.skipped}`;

        if (data.errors && data.errors.length) {
          msg += `\nErrors: ${data.errors.length}`;
          console.error("Archive errors:", data.errors);
        }

        alert(msg);

      } catch (error) {
        console.error("Mass archive error:", error);
        alert("Error: " + error.message);
      } finally {
        generateMonthBtn.disabled = false;
      }
    });
  }

  // Scale ticket export
  (function initScaleTicketExport() {
    function setCurrentTime() {
      const now = new Date();
      const formattedTime = now.toLocaleTimeString("en-US", { hour12: false }).slice(0, 5);
      const timeInput = byId("deal_time");
      if (timeInput) timeInput.value = formattedTime;
    }
    setCurrentTime();

    window.fetchDealData = function () {
      const ticketNumberElement = byId("ticket_number");
      if (!ticketNumberElement) return;
      const ticketNumber = ticketNumberElement.value;
      if (!ticketNumber || ticketNumber.length < 3) return;

      fetchJSON(u(`get-deal-by-ticket/?ticket_number=${encodeURIComponent(ticketNumber)}`))
        .then((data) => {
          if (!data.success) { alert("Deal not found for this Scale Ticket."); return; }
          const d = data.deal;
          const setVal = (id, val) => { const el = byId(id); if (el) el.value = val; };

          setVal("selectedDealId",                  d.id);
          setVal("scaleticket_date",                d.date);
          setVal("scaleticket_received_quantity",   d.received_quantity);
          setVal("pallets",                         d.received_pallets);
          setVal("supplier_name",                   d.supplier_name);
          setVal("scaleticket_grade",               d.grade);

          const randomTareWeight = 5170 + Math.floor(Math.random() * 301);
          setVal("tare_weight", randomTareWeight);

          const netWeight = toFloat(d.net_weight_str || d.received_quantity * 1000 || 0);
          setVal("net_weight",   netWeight);
          setVal("gross_weight", randomTareWeight + netWeight);
        })
        .catch((err) => console.error("Error fetching deal data:", err));
    };

    window.exportScaleTicket = function (event) {
      event.preventDefault();
      const getVal = (id, def = "") => { const el = byId(id); if (!el) { console.warn(`⚠️ '${id}' not found`); return def; } return el.value || def; };
      const ticketNumber = getVal("ticket_number");
      if (!ticketNumber) { alert("⚠️ Please enter a scale ticket number before exporting."); return; }

      const dealTime    = getVal("deal_time",    "N/A");
      const licencePlate= getVal("licence_plate","N/A");
      const tareWeight  = toFloat(getVal("tare_weight","0"));
      const netWeight   = toFloat(getVal("net_weight",  "0"));
      const grossWeight = tareWeight + netWeight;

      const url = u(
        `export-scale-ticket/?ticket_number=${encodeURIComponent(ticketNumber)}`
        + `&time=${encodeURIComponent(dealTime)}`
        + `&licence_plate=${encodeURIComponent(licencePlate)}`
        + `&gross_weight=${encodeURIComponent(grossWeight)}`
        + `&tare_weight=${encodeURIComponent(tareWeight)}`
        + `&net_weight=${encodeURIComponent(netWeight)}`
      );

      const a = document.createElement("a");
      a.href = url;
      a.download = `Ticket #${ticketNumber}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    };

    const exportBtn = byId("exportScaleTicketBtn");
    if (exportBtn) {
      exportBtn.addEventListener("click", exportScaleTicket);
      console.log("✅ Export button connected.");
    } else {
      console.error("🚨 exportScaleTicketBtn NOT FOUND!");
    }

    const licencePlates = ["SY1341", "WB3291", "153"];
    const licenceSelect = byId("licence_plate");
    if (licenceSelect) {
      const placeholder = document.createElement("option");
      placeholder.value = ""; placeholder.textContent = "Select Licence Plate";
      placeholder.disabled = true; placeholder.selected = true;
      licenceSelect.appendChild(placeholder);
      licencePlates.forEach((plate) => {
        const opt = document.createElement("option");
        opt.value = plate; opt.textContent = plate;
        licenceSelect.appendChild(opt);
      });
    } else {
      console.error("🚨 licence_plate NOT FOUND!");
    }
  })();

  // ===== Автоподстановка цен =====
  const supplierEl = byId("supplier");
  const buyerEl    = byId("buyer");
  const gradeEl    = byId("grade");

  supplierEl && supplierEl.addEventListener("change", () => { fetchSupplierPrice(); fetchBuyerPrice(); });
  buyerEl    && buyerEl.addEventListener("change", fetchBuyerPrice);
  gradeEl    && gradeEl.addEventListener("change", () => { fetchSupplierPrice(); fetchBuyerPrice(); });

  function fetchSupplierPrice() {
    const supplierId = byId("supplier")?.value;
    const grade      = byId("grade")?.value;
    if (supplierId && grade) {
      fetchJSON(u(`api/get_price/?supplier_id=${encodeURIComponent(supplierId)}&grade=${encodeURIComponent(grade)}`))
        .then((data) => { const f = byId("supplier_price"); if (f) f.value = data.price || ""; })
        .catch((err) => console.error("Ошибка при получении цены:", err));
    }
  }

  function fetchBuyerPrice() {
    const buyerId = byId("buyer")?.value;
    const grade   = byId("grade")?.value;
    if (buyerId && grade) {
      fetchJSON(u(`api/get_buyer_price/?buyer_id=${encodeURIComponent(buyerId)}&grade=${encodeURIComponent(grade)}`))
        .then((data) => { const f = byId("buyer_price"); if (f) f.value = data.price || ""; })
        .catch((err) => console.error("Ошибка при получении цены покупателя:", err));
    }
  }
});

// ==========================================================================
//  renderDealAnalytics — заполняет и анимирует карточку аналитики
// ==========================================================================
function renderDealAnalytics(data) {
  const isLoss = data.profit < 0;

  // ── Profit hero ──────────────────────────────────────────────────────────
  const profitEl = byId("daProfit");
  if (profitEl) {
    profitEl.textContent = (isLoss ? "−" : "+") + "$" + Math.abs(data.profit).toFixed(2);
    profitEl.className   = "da-hero-value da-profit " + (isLoss ? "da-neg" : "da-pos");
  }

  const perTonEl = byId("daProfitPerTon");
  if (perTonEl) {
    perTonEl.textContent = (data.profitPerTon >= 0 ? "+" : "") + data.profitPerTon.toFixed(2) + " / MT";
    perTonEl.className   = "da-hero-badge" + (isLoss ? "" : " da-badge-pos");
  }

  // ── Статус-чип ───────────────────────────────────────────────────────────
  const chip = byId("daProfitChip");
  if (chip) {
    chip.textContent = isLoss ? "Loss" : "Profit";
    chip.className   = "da-status-chip " + (isLoss ? "da-chip-loss" : "da-chip-profit");
  }

  // ── Метрики ──────────────────────────────────────────────────────────────
  const spreadEl = byId("daSpreadPerTon");
  if (spreadEl) {
    spreadEl.textContent = "$" + data.spreadPerTon.toFixed(2);
    spreadEl.className   = "da-metric-val da-pos";
  }

  const transEl = byId("daTransportPerTon");
  if (transEl) {
    transEl.textContent = "$" + data.transportPerTon.toFixed(2);
    transEl.className   = "da-metric-val da-neg";
  }

  const varEl = byId("daVariance");
  if (varEl) varEl.textContent = (data.variance >= 0 ? "+" : "") + data.variance.toFixed(3) + " MT";

  const palletEl = byId("daAvgPalletWeight");
  if (palletEl) palletEl.textContent = data.avgPalletWeight.toFixed(0) + " kg";

  // ── Transport share chip ─────────────────────────────────────────────────
  const tsChip = byId("daTransportShareChip");
  if (tsChip) tsChip.textContent = data.transportShare.toFixed(1) + " %";

  // ── Transport bar (анимация) ─────────────────────────────────────────────
  const barFill = byId("daTransportBarFill");
  if (barFill) {
    barFill.style.width = "0%";                       // сброс
    setTimeout(() => {
      barFill.style.width = Math.min(data.transportShare, 100) + "%";
    }, 120);
  }

  // ── Donut: spread efficiency ──────────────────────────────────────────────
  const efficiency = data.spreadPerTon > 0
    ? Math.max(0, ((data.spreadPerTon - data.transportPerTon) / data.spreadPerTon) * 100)
    : 0;

  const donutFill = byId("daDonutFill");
  if (donutFill) {
    donutFill.style.strokeDasharray = "0 100";        // сброс
    donutFill.style.stroke = efficiency >= 50 ? "#2dd4bf" : "#fbbf24";
    setTimeout(() => {
      donutFill.style.strokeDasharray = efficiency.toFixed(1) + " 100";
    }, 150);
  }

  const effPct = byId("daEfficiencyPct");
  if (effPct) {
    effPct.textContent = efficiency.toFixed(0) + "%";
    effPct.style.color = efficiency >= 50 ? "#2dd4bf" : "#fbbf24";
  }

  // ── Variance segments ─────────────────────────────────────────────────────
  const segs  = document.querySelectorAll("#daVarianceSegs .da-seg");
  const ratio = Math.min(Math.abs(data.variance) / 2, 1);   // 2 MT = 100%
  const count = Math.round(ratio * segs.length);
  segs.forEach((s, i) => {
    s.className = "da-seg" + (i < count ? " da-seg-active" : "");
  });

  // ── Spark-линия: цвет и сброс анимации ───────────────────────────────────
  const sparkLine = byId("daSparkLine");
  const sparkArea = byId("daSparkArea");

  if (sparkLine) {
    sparkLine.className = "da-spark-line " + (isLoss ? "da-spark-loss" : "da-spark-profit");
    sparkLine.style.animation = "none";
    void sparkLine.getBoundingClientRect();   // reflow
    sparkLine.style.animation = "";
  }
  if (sparkArea) {
    sparkArea.setAttribute("fill", isLoss ? "url(#daSparkGrad)" : "url(#daSparkGradGreen)");
    sparkArea.style.animation = "none";
    void sparkArea.getBoundingClientRect();
    sparkArea.style.animation = "";
  }
}