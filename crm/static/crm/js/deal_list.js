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

// ===== Main =====
document.addEventListener("DOMContentLoaded", () => {
  console.log("Scale URL ->", u("api/scale-ticket-counters/"));

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

      if (
        !receivedQuantityElement ||
        !buyerPriceElement ||
        !supplierPriceElement ||
        !transportCostElement
      ) {
        console.error("Элементы формы не найдены!");
        return;
      }

      const received_quantity = toFloat(receivedQuantityElement.value);
      const buyer_price = toFloat(buyerPriceElement.value);
      const supplier_price = toFloat(supplierPriceElement.value);
      const transport_cost = toFloat(transportCostElement.value);
      const shipped_quantity = toFloat(byId("shipped_quantity")?.value);

      // локальные расчёты (бэкенд всё равно пересчитает)
      const total_amount = shipped_quantity * buyer_price;
      const supplier_total = received_quantity * supplier_price;
      const total_income_loss = total_amount - supplier_total - transport_cost;
      void total_income_loss; // чтобы линтер не ругался

      const data = {
        date: byId("date")?.value,
        supplier: toInt(byId("supplier")?.value),
        buyer: toInt(byId("buyer")?.value),
        grade: byId("grade")?.value,
        shipped_quantity: shipped_quantity,
        shipped_pallets: toInt(byId("shipped_pallets")?.value),
        received_quantity: received_quantity,
        received_pallets: toInt(byId("received_pallets")?.value),
        supplier_price: supplier_price,
        buyer_price: buyer_price,
        transport_cost: transport_cost,
        transport_company: toInt(byId("transport_company")?.value),
        scale_ticket: byId("scale_ticket")?.value,
      };

      fetchJSON(u("api/deals/"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify(data),
      })
        .then((data) => {
          console.log("Deal created:", data);

          const tbody = byId("dealTable")?.getElementsByTagName("tbody")?.[0];
          if (tbody) {
            const tr = tbody.insertRow();
            tr.classList.add("deal-row");
            tr.dataset.id = data.id ?? "";
            tr.innerHTML = `
              <td>${data.date ?? ""}</td>
              <td>${data.supplier_name ?? ""}</td>
              <td>${data.buyer ?? ""}</td>
              <td>${data.grade ?? ""}</td>
              <td>${data.shipped_quantity ?? ""} / ${data.shipped_pallets ?? ""}</td>
              <td>${data.received_quantity ?? ""} / ${data.received_pallets ?? ""}</td>
              <td>${data.supplier_price ?? ""}</td>
              <td>${data.supplier_total ?? ""}</td>
              <td>${data.buyer_price ?? ""}</td>
              <td>${data.total_amount ?? ""}</td>
              <td>${data.transport_cost ?? ""}</td>
              <td>${data.transport_company?.name ?? data.transport_company ?? ""}</td>
              <td>${data.total_income_loss ?? ""}</td>
              <td>${data.scale_ticket ?? ""}</td>
              
               <td>
                ${
                  data.scale_ticket
                    ? `<button class="scale-ticket-status-btn ${data.scale_ticket_sent ? "sent" : "not-sent"}"
                               data-path="${data.scale_ticket_relative_path || ""}">
                         ${data.scale_ticket_sent ? "Sent" : "Send"}
                       </button>`
                    : `<span class="no-scale-ticket">N/A</span>`
                }
              </td>
              <td>${data.total_income_loss ?? ""}</td>
            `;
            attachDealRowHandler(tr);
            attachScaleTicketHandlers(tr);
          }

          byId("dealFormSidebar") && (byId("dealFormSidebar").style.width = "0");
          dealForm.reset();

          return fetch(u("api/scale-ticket-counters/increment/"), {
            method: "POST",
            headers: { "X-CSRFToken": csrftoken },
          });
        })
        .catch((err) => console.error("Error (create deal):", err));
    });
  }

  // --- Открыть сайдбар деталей по клику на строку
   function attachDealRowHandler(row) {
    row.addEventListener("click", () => {
      const dealId = row.dataset.id;
      if (!dealId) return;

      fetchJSON(u(`deals/${dealId}/`))
        .then((data) => {
          byId("dealDate") && (byId("dealDate").innerText = data.date ?? "");
          byId("dealSupplier") &&
            (byId("dealSupplier").innerText = data.supplier_name ?? "");
          byId("dealBuyer") &&
            (byId("dealBuyer").innerText = data.buyer_name ?? "");
          byId("dealGrade") && (byId("dealGrade").innerText = data.grade ?? "");
          byId("dealTotalAmount") &&
            (byId("dealTotalAmount").innerText = data.total_amount ?? "");
          byId("dealScaleTicket") &&
            (byId("dealScaleTicket").innerText = data.scale_ticket ?? "");

          // 🔹 KPI блок

          const profit = Number(data.total_income_loss ?? 0);
          const profitPerTon = data.profit_per_ton != null ? Number(data.profit_per_ton) : null;
          const transportPerTon = data.transport_per_ton != null ? Number(data.transport_per_ton) : null;
          const transportShare = data.transport_share != null ? Number(data.transport_share) : null;
          const spreadPerTon = data.spread_per_ton != null ? Number(data.spread_per_ton) : null;
          const varianceMt = data.variance_mt != null ? Number(data.variance_mt) : null;
          const avgPalletKg = data.avg_pallet_weight_kg != null ? Number(data.avg_pallet_weight_kg) : null;

          // Прибыль
          if (byId("daProfit")) {
            const el = byId("daProfit");
            el.classList.remove("da-profit-positive", "da-profit-negative");
            el.innerText = `${profit >= 0 ? "+" : "-"}$${Math.abs(profit).toFixed(2)}`;
            if (profit > 0) el.classList.add("da-profit-positive");
            if (profit < 0) el.classList.add("da-profit-negative");
          }

          // Прибыль на тонну
          if (byId("daProfitPerTon")) {
            byId("daProfitPerTon").innerText =
              profitPerTon != null ? `$${profitPerTon.toFixed(2)} / MT` : "N/A";
          }

          // Спред
          if (byId("daSpreadPerTon")) {
            byId("daSpreadPerTon").innerText =
              spreadPerTon != null ? `$${spreadPerTon.toFixed(2)} / MT` : "N/A";
          }

          // Транспорт на тонну
          if (byId("daTransportPerTon")) {
            byId("daTransportPerTon").innerText =
              transportPerTon != null ? `$${transportPerTon.toFixed(2)} / MT` : "N/A";
          }

          // Доля логистики
          if (byId("daTransportShareChip")) {
            const chip = byId("daTransportShareChip");
            chip.classList.remove("da-chip--green", "da-chip--yellow", "da-chip--red");

            if (transportShare == null) {
              chip.innerText = "N/A";
            } else {
              chip.innerText = `${transportShare.toFixed(1)} %`;

              if (transportShare < 15) {
                chip.classList.add("da-chip--green");
              } else if (transportShare < 25) {
                chip.classList.add("da-chip--yellow");
              } else {
                chip.classList.add("da-chip--red");
              }
            }
          }

          // Отклонение по весу
          if (byId("daVariance")) {
            byId("daVariance").innerText =
              varianceMt != null ? `${varianceMt.toFixed(3)} MT` : "N/A";
          }

          // Средний вес паллеты
          if (byId("daAvgPalletWeight")) {
            byId("daAvgPalletWeight").innerText =
              avgPalletKg != null ? `${avgPalletKg.toFixed(0)} kg` : "N/A";
          }

          const sidebar = byId("viewDealSidebar");
          if (sidebar) {
            sidebar.dataset.dealId = dealId;
            sidebar.style.width = "400px";
          }
        })
        .catch((err) => console.error("Error fetching deal details:", err));
    });
    function attachScaleTicketHandlers(root) {
      const scope = root || document;
      const buttons = scope.querySelectorAll(".scale-ticket-status-btn");

      buttons.forEach((btn) => {
        if (btn.dataset.bound === "1") return;
        btn.dataset.bound = "1";

        btn.addEventListener("click", () => {
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
              if (!data.success) {
                throw new Error(data.error || "Send failed");
              }
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

    document.addEventListener("DOMContentLoaded", () => {
      attachScaleTicketHandlers(document);
    });

  // сразу после загрузки страницы:
  attachScaleTicketHandlers(document);

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
  // открыть сайдбар
    function openDealSidebar() {
      const sidebar = document.getElementById("viewDealSidebar");
      sidebar.classList.add("open");
    }

    // закрыть сайдбар
    function closeDealSidebar() {
      const sidebar = document.getElementById("viewDealSidebar");
      sidebar.classList.remove("open");
    }

    // обработчик кнопки
    document.getElementById("closeViewDealSidebarBtn")?.addEventListener("click", closeDealSidebar);
    // Конфиг, похожий на пропсы GlassSurface:
    const glassProps = {
      displace: 15,             // влияет на baseFrequency
      distortionScale: -150,    // берем модуль => scale
      redOffset: 5,
      greenOffset: 15,
      blueOffset: 25,
      brightness: 0.60,         // 0..1 (60%)
      opacity: 0.80,            // 0..1
      mixBlendMode: "screen"    // screen / lighten / overlay / normal
    };

    function applyGlassProps(el, props){
      if(!el) return;
      // CSS vars на .glass-panel
      el.style.setProperty('--rgb-r', `${props.redOffset||0}px`);
      el.style.setProperty('--rgb-g', `${props.greenOffset||0}px`);
      el.style.setProperty('--rgb-b', `${props.blueOffset||0}px`);
      el.style.setProperty('--brightness', String(props.brightness ?? 1));
      el.style.setProperty('--glass-opacity', String(props.opacity ?? 0.85));
      el.style.setProperty('--mix', props.mixBlendMode || 'screen');

      // SVG filter tuning:
      const filter = document.querySelector('#glass-disp');
      const turb = filter?.querySelector('feTurbulence');
      const disp = filter?.querySelector('feDisplacementMap');

      if(turb){
        // «displace»: чем больше значение, тем выше baseFrequency (0.004..0.02)
        const base = 0.004 + Math.min(Math.max((props.displace||0)/100, 0), 0.12);
        turb.setAttribute('baseFrequency', base.toFixed(4));
      }
      if(disp){
        const s = Math.abs(props.distortionScale ?? 10);
        disp.setAttribute('scale', String(s));
      }
    }

    // Применяем при загрузке
    document.addEventListener('DOMContentLoaded', () => {
      const glass = document.querySelector('#viewDealSidebar .glass-panel');
      applyGlassProps(glass, glassProps);
    });



  // --- Включить режим редактирования
  const editDealBtn = byId("editDealBtn");
  if (editDealBtn) {
    editDealBtn.addEventListener("click", () => {
      const sidebar = byId("viewDealSidebar");
      sidebar && sidebar.classList.add("editing");
      const details = byId("dealDetailsContent");
      const form = byId("editDealForm");
      details && (details.style.display = "none");
      form && (form.style.display = "block");

      const dealId = byId("viewDealSidebar")?.dataset.dealId;
      if (!dealId) return;

      fetchJSON(u(`deals/${dealId}/`))
        .then((data) => {
          byId("editDate") && (byId("editDate").value = data.date ?? "");
          byId("editSupplier") &&
            (byId("editSupplier").value = data.supplier_id ?? "");
          byId("editBuyer") && (byId("editBuyer").value = data.buyer_id ?? "");
          byId("editGrade") && (byId("editGrade").value = data.grade ?? "");
          byId("editShippedQuantity") &&
            (byId("editShippedQuantity").value = data.shipped_quantity ?? "");
          byId("editShippedPallets") &&
            (byId("editShippedPallets").value = data.shipped_pallets ?? "");
          byId("editReceivedQuantity") &&
            (byId("editReceivedQuantity").value = data.received_quantity ?? "");
          byId("editReceivedPallets") &&
            (byId("editReceivedPallets").value = data.received_pallets ?? "");
          byId("editSupplierPrice") &&
            (byId("editSupplierPrice").value = data.supplier_price ?? "");
          byId("editBuyerPrice") &&
            (byId("editBuyerPrice").value = data.buyer_price ?? "");
          byId("editTransportCost") &&
            (byId("editTransportCost").value = data.transport_cost ?? "");
          byId("editTransportCompany") &&
            (byId("editTransportCompany").value = data.transport_company_id ?? "");
          byId("editScaleTicket") &&
            (byId("editScaleTicket").value = data.scale_ticket ?? "");
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
      const details = byId("dealDetailsContent");
      const form = byId("editDealForm");
      details && (details.style.display = "block");
      form && (form.style.display = "none");
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
        date: byId("editDate")?.value,
        supplier: toInt(byId("editSupplier")?.value),
        buyer: toInt(byId("editBuyer")?.value),
        grade: byId("editGrade")?.value,
        shipped_quantity: toFloat(byId("editShippedQuantity")?.value),
        shipped_pallets: toInt(byId("editShippedPallets")?.value),
        received_quantity: toFloat(byId("editReceivedQuantity")?.value),
        received_pallets: toInt(byId("editReceivedPallets")?.value),
        supplier_price: toFloat(byId("editSupplierPrice")?.value),
        buyer_price: toFloat(byId("editBuyerPrice")?.value),
        transport_cost: toFloat(byId("editTransportCost")?.value),
        transport_company: toInt(byId("editTransportCompany")?.value),
        scale_ticket: byId("editScaleTicket")?.value,
      };

      fetchJSON(u(`deals/${dealId}/edit/`), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify(payload),
      })
        .then((data) => {
          const sidebar = byId("viewDealSidebar");
          sidebar && sidebar.classList.remove("editing");
          alert("Changes saved successfully!");
          byId("dealDate") && (byId("dealDate").innerText = data.date ?? "");
          byId("dealSupplier") &&
            (byId("dealSupplier").innerText = data.supplier ?? "");
          byId("dealBuyer") &&
            (byId("dealBuyer").innerText = data.buyer ?? "");
          byId("dealGrade") &&
            (byId("dealGrade").innerText = data.grade ?? "");
          byId("dealTotalAmount") &&
            (byId("dealTotalAmount").innerText = data.total_amount ?? "");

          const details = byId("dealDetailsContent");
          const form = byId("editDealForm");
          details && (details.style.display = "block");
          form && (form.style.display = "none");
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
            const sidebar = byId("viewDealSidebar");
            if (sidebar) sidebar.style.width = "0";
            const row = document.querySelector(`.deal-row[data-id="${dealId}"]`);
            row && row.remove();
          })
          .catch((err) => console.error("Error deleting deal:", err));
      }
    });
  }

  // ===== Scale ticket sidebar helpers =====
  window.openScaleTicketSidebarFromDeal = function () {
    const scaleTicket = byId("dealScaleTicket")?.innerText;
    if (!scaleTicket || scaleTicket === "N/A") {
      alert("⛔ Опа, нема номера Scale Ticket.");
      return;
    }
    openScaleTicketSidebar();
    setTimeout(() => {
      const input = byId("ticket_number");
      if (input) {
        input.value = scaleTicket;
        fetchDealData();
      } else {
        console.error("⚠️ Отакої, нема ticket_number!");
      }
    }, 300);
  };

  // --- Sidebar open/close
  (function initScaleTicketSidebar() {
    console.log("✅ Script loaded: Scale Ticket Sidebar");
    const sidebar = byId("scaleTicketSidebar");
    if (!sidebar) {
      console.error("⚠️ Scale Ticket Sidebar НЕ найден в DOM! Проверь ID.");
      return;
    }
    window.openScaleTicketSidebar = function () {
      sidebar.style.display = "block";
      setTimeout(() => sidebar.classList.add("open"), 10);
    };
    window.closeScaleTicketSidebar = function () {
      sidebar.classList.remove("open");
      setTimeout(() => (sidebar.style.display = "none"), 300);
    };
    const openBtn = document.querySelector("button[onclick='openScaleTicketSidebar()']");
    openBtn && openBtn.addEventListener("click", openScaleTicketSidebar);
    const closeBtn = document.querySelector("#scaleTicketSidebar .close-btn");
    closeBtn && closeBtn.addEventListener("click", closeScaleTicketSidebar);
  })();

  // --- Scale ticket export / fetch
  (function initScaleTicketExport() {
    console.log("✅ Script loaded: Scale Ticket Export");

    function setCurrentTime() {
      const now = new Date();
      const formattedTime = now
        .toLocaleTimeString("en-US", { hour12: false })
        .slice(0, 5);
      const timeInput = byId("deal_time");
      timeInput ? (timeInput.value = formattedTime) : console.warn("⚠️ Поле 'time' не найдено в DOM.");
    }
    setCurrentTime();

    window.fetchDealData = function () {
      const ticketNumberElement = byId("ticket_number");
      if (!ticketNumberElement) {
        console.error("🚨 Ошибка: поле 'ticket_number' не найдено!");
        return;
      }
      const ticketNumber = ticketNumberElement.value;
      if (!ticketNumber || ticketNumber.length < 3) {
        console.warn("⚠️ Введите минимум 3 символа для поиска сделки.");
        return;
      }

      console.log(`🔍 Fetching deal data for ticket: ${ticketNumber}`);
      fetchJSON(u(`get-deal-by-ticket/?ticket_number=${encodeURIComponent(ticketNumber)}`))
        .then((data) => {
          if (!data.success) {
            console.warn("❌ Deal not found for this Scale Ticket.");
            alert("Deal not found for this Scale Ticket.");
            return;
          }

          const d = data.deal;
          const setVal = (id, val) => {
            const el = byId(id);
            el ? (el.value = val) : console.warn(`⚠️ Поле '${id}' не найдено в DOM.`);
          };

          setVal("selectedDealId", d.id);
          setVal("scaleticket_date", d.date);
          setVal("scaleticket_received_quantity", d.received_quantity);
          setVal("pallets", d.received_pallets);
          setVal("supplier_name", d.supplier_name);
          setVal("scaleticket_grade", d.grade);

          const randomTareWeight = 5170 + Math.floor(Math.random() * 301);
          setVal("tare_weight", randomTareWeight);

          const netWeight = toFloat(d.net_weight_str || d.received_quantity * 1000 || 0);
          setVal("net_weight", netWeight);

          const grossWeight = randomTareWeight + netWeight;
          setVal("gross_weight", grossWeight);

          console.log(
            `📌 Пересчет весов: Tare = ${randomTareWeight}, Net = ${netWeight}, Gross = ${grossWeight}`
          );
        })
        .catch((err) => console.error("🚨 Error fetching deal data:", err));
    };

    window.exportScaleTicket = function (event) {
      event.preventDefault();

      const getVal = (id, def = "") => {
        const el = byId(id);
        if (!el) {
          console.warn(`⚠️ Поле '${id}' не найдено в DOM.`);
          return def;
        }
        return el.value || def;
      };

      const ticketNumber = getVal("ticket_number");
      if (!ticketNumber) {
        alert("⚠️ Please enter a scale ticket number before exporting.");
        return;
      }

      const dealTime = getVal("deal_time", "N/A");
      const licencePlate = getVal("licence_plate", "N/A");
      const tareWeight = toFloat(getVal("tare_weight", "0"));
      const netWeight = toFloat(getVal("net_weight", "0"));
      const grossWeight = tareWeight + netWeight;

      console.log(
        `📂 Exporting Scale Ticket: ${ticketNumber}, Time: ${dealTime}, Licence: ${licencePlate}, Gross: ${grossWeight}, Tare: ${tareWeight}, Net: ${netWeight}`
      );

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
      console.error("🚨 Export button NOT FOUND! Проверь ID: exportScaleTicketBtn");
    }

    const licencePlates = ["SY1341", "WB3291", "153"];
    const licenceSelect = byId("licence_plate");
    if (licenceSelect) {
      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "Select Licence Plate";
      placeholder.disabled = true;
      placeholder.selected = true;
      licenceSelect.appendChild(placeholder);

      licencePlates.forEach((plate) => {
        const opt = document.createElement("option");
        opt.value = plate;
        opt.textContent = plate;
        licenceSelect.appendChild(opt);
      });
    } else {
      console.error("🚨 Licence plate dropdown (licence_plate) NOT FOUND!");
    }
  })();

  // ===== Автоподстановка цен =====
  const supplierEl = byId("supplier");
  const buyerEl = byId("buyer");
  const gradeEl = byId("grade");

  supplierEl &&
    supplierEl.addEventListener("change", () => {
      fetchSupplierPrice();
      fetchBuyerPrice();
    });
  buyerEl && buyerEl.addEventListener("change", fetchBuyerPrice);
  gradeEl &&
    gradeEl.addEventListener("change", () => {
      fetchSupplierPrice();
      fetchBuyerPrice();
    });

  function fetchSupplierPrice() {
    const supplierId = byId("supplier")?.value;
    const grade = byId("grade")?.value;
    if (supplierId && grade) {
      fetchJSON(
        u(`api/get_price/?supplier_id=${encodeURIComponent(supplierId)}&grade=${encodeURIComponent(grade)}`)
      )
        .then((data) => {
          const priceField = byId("supplier_price");
          if (!priceField) return;
          priceField.value = data.price ? data.price : "";
        })
        .catch((err) => console.error("Ошибка при получении цены:", err));
    }
  }

  function fetchBuyerPrice() {
    const buyerId = byId("buyer")?.value;
    const grade = byId("grade")?.value;
    if (buyerId && grade) {
      fetchJSON(
        u(`api/get_buyer_price/?buyer_id=${encodeURIComponent(buyerId)}&grade=${encodeURIComponent(grade)}`)
      )
        .then((data) => {
          const priceField = byId("buyer_price");
          if (!priceField) return;
          priceField.value = data.price || "";
        })
        .catch((err) => console.error("Ошибка при получении цены покупателя:", err));
    }
  }
});
