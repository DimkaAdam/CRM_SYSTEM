/* =========================
   Base URL helper (/crm)
   ========================= */
function u(path) {
  return `/crm/${path}`.replace(/\/+/g, "/");
}

/* =========================
   CSRF (for Django POST/DELETE)
   ========================= */
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return "";
}

function csrfHeaders(extra = {}) {
  return {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken"),
    ...extra,
  };
}

/* =========================
   Global calendar instance
   ========================= */
let calendar = null;

/* =========================
   DOM Ready
   ========================= */
document.addEventListener("DOMContentLoaded", function () {
  /* -------------------------
     Elements
     ------------------------- */
  const generateBolBtn = document.getElementById("generate-bol-btn");
  const bolModal = document.getElementById("bol-modal");
  const closeBolModalBtn = document.getElementById("close-bol-modal");

  const toggleBtn = document.getElementById("toggle-calendar-btn");
  const calendarWrapper = document.getElementById("calendar-wrapper");
  const calendarEl = document.getElementById("calendar");

  const shipmentListContainer = document.getElementById("shipment-list");

  const addShipmentForm = document.getElementById("add-shipment-form");
  const repeatCheckbox = document.getElementById("is_recurring");
  const recurrenceSelect = document.getElementById("recurrence_type");

  /* -------------------------
     Repeat toggle
     ------------------------- */
  if (recurrenceSelect) recurrenceSelect.disabled = true;

  if (repeatCheckbox && recurrenceSelect) {
    repeatCheckbox.addEventListener("change", function () {
      recurrenceSelect.disabled = !this.checked;
    });
  }

  /* -------------------------
     Open BOL modal
     ------------------------- */
  if (generateBolBtn && bolModal) {
    generateBolBtn.addEventListener("click", function () {
      bolModal.style.display = "block";

      // Ensure fields exist in DOM then load counters
      const checkFieldsReady = setInterval(() => {
        const bolInput = document.getElementById("bol-number");
        const loadInput = document.getElementById("load-number");

        if (bolInput && loadInput) {
          clearInterval(checkFieldsReady);
          loadDealDetails();
        }
      }, 50);
    });
  }

  /* -------------------------
     Close BOL modal
     ------------------------- */
  if (closeBolModalBtn && bolModal) {
    closeBolModalBtn.addEventListener("click", function () {
      bolModal.style.display = "none";
    });
  }

  /* -------------------------
     Toggle calendar visibility
     ------------------------- */
  if (toggleBtn && calendarWrapper) {
    toggleBtn.addEventListener("click", function () {
      const isHidden =
        calendarWrapper.style.display === "none" || calendarWrapper.style.display === "";
      if (isHidden) {
        calendarWrapper.style.display = "block";
        toggleBtn.textContent = "Hide Calendar";
      } else {
        calendarWrapper.style.display = "none";
        toggleBtn.textContent = "Open Calendar";
      }
    });
  }

  /* -------------------------
     FullCalendar init
     (We manage events manually in loadShipments)
     ------------------------- */
  if (calendarEl) {
    calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: "timeGridWeek",
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "dayGridMonth,timeGridWeek,timeGridDay",
      },
      editable: false,
      selectable: true,
      nowIndicator: true,

      eventClick: function (info) {
        if (!confirm("Delete this shipment?")) return;

        const shipmentId = info.event.id;

        fetch(u(`api/scheduled-shipments/delete/${shipmentId}/`), {
          method: "DELETE",
          headers: csrfHeaders(),
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.status === "deleted") {
              info.event.remove();
              removeShipmentFromList(shipmentId);
              alert("Shipment deleted.");
            } else {
              alert("Delete failed.");
            }
          })
          .catch((err) => {
            console.error("Delete error:", err);
            alert("Server error.");
          });
      },
    });

    calendar.render();
  }

  /* -------------------------
     Load data (suppliers, buyers, carrier, grades)
     ------------------------- */
  loadData();

  /* -------------------------
     Load shipments list + calendar events
     ------------------------- */
  loadShipments();

  /* -------------------------
     Add shipment submit
     ------------------------- */
  if (addShipmentForm) {
    addShipmentForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const supplier = document.getElementById("supplier")?.value || "";
      const buyer = document.getElementById("buyer")?.value || "";
      const date = document.getElementById("shipment-date")?.value || "";
      const time = document.getElementById("shipment-time")?.value || "";
      const grade = document.getElementById("shipment-grade")?.value || "";
      const isRecurring = document.getElementById("is_recurring")?.checked || false;
      const recurrenceType = document.getElementById("recurrence_type")?.value || "";

      if (!supplier || !buyer || !date || !time || !grade) {
        alert("Please fill in all required fields.");
        return;
      }

      const shipmentData = {
        supplier: supplier,
        buyer: buyer,
        datetime: `${date}T${time}:00`,
        grade: grade,
        is_recurring: isRecurring,
        recurrence_type: recurrenceType,
        recurrence_day: new Date(date).getDay(),
      };

      fetch(u("api/scheduled-shipments/add/"), {
        method: "POST",
        headers: csrfHeaders(),
        body: JSON.stringify(shipmentData),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.status === "success") {
            alert("Shipment added.");
            loadShipments();
          } else {
            alert("Error adding shipment.");
          }
        })
        .catch((err) => {
          console.error("Add shipment error:", err);
          alert("Server error.");
        });
    });
  }

  /* -------------------------
     BOL form submit -> PDF
     ------------------------- */
  const bolForm = document.getElementById("bol-form");
  if (bolForm) {
    bolForm.addEventListener("submit", function (event) {
      event.preventDefault();
      generateBOLPDF();
    });
  }

  /* -------------------------
     BOL supplier/buyer address autofill (if using onchange in HTML, this is optional)
     ------------------------- */
  const bolSupplierSelect = document.getElementById("bolSupplier");
  if (bolSupplierSelect) {
    bolSupplierSelect.addEventListener("change", function () {
      setSupplierAddress(this);
    });
  }

  const bolBuyerSelect = document.getElementById("bolBuyer");
  if (bolBuyerSelect) {
    bolBuyerSelect.addEventListener("change", function () {
      setBuyerAddress(this);
    });
  }

  /* -------------------------
     Event delegation for dynamic buttons
     ------------------------- */
  document.addEventListener("click", function (e) {
    // Add commodity row
    if (e.target && e.target.id === "add-commodity") {
      addCommodityRow();
      return;
    }

    // Remove commodity row
    if (e.target && e.target.classList && e.target.classList.contains("remove-commodity")) {
      const tr = e.target.closest("tr");
      if (tr) tr.remove();
      return;
    }

    // Mark shipment done
    if (e.target && e.target.classList && e.target.classList.contains("mark-done-btn")) {
      const shipmentId = e.target.dataset.id;
      if (!shipmentId) return;

      fetch(u(`api/scheduled-shipments/done/${shipmentId}/`), {
        method: "POST",
        headers: csrfHeaders(),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.status === "done") {
            alert("Shipment marked as done.");
            loadShipments();
          } else {
            alert("Failed to mark as done.");
          }
        })
        .catch((err) => {
          console.error("Mark done error:", err);
          alert("Server error.");
        });

      return;
    }
  });

  /* =========================
     Functions
     ========================= */

  function addCommodityRow() {
    const tbody = document.getElementById("commodity-body");
    if (!tbody) return;

    const row = document.createElement("tr");
    // Must match your table header:
    // Qty | Handling | Package | Weight | HM | Description | DIMS | Class | NMFC # | (remove)
    row.innerHTML = `
      <td><input type="number" name="qty[]" required></td>
      <td><input type="text" name="handling[]" required></td>
      <td><input type="text" name="pkg[]" required></td>
      <td><input type="number" name="weight[]" required></td>
      <td><input type="text" name="hm[]"></td>
      <td><input type="text" name="description[]" required></td>
      <td><input type="text" name="dims[]"></td>
      <td><input type="text" name="class[]"></td>
      <td><input type="text" name="nmfc[]"></td>
      <td><button type="button" class="remove-commodity">🗑</button></td>
    `;
    tbody.appendChild(row);
  }

  function removeShipmentFromList(shipmentId) {
    if (!shipmentListContainer) return;
    const nodes = shipmentListContainer.querySelectorAll(`[data-id="${shipmentId}"]`);
    nodes.forEach((n) => n.remove());
  }

  function loadData() {
    Promise.all([
      fetch(u("api/companies-by-type/")).then((res) => res.json()),
      fetch(u("api/grades/")).then((res) => res.json()),
    ])
      .then(([companiesData, gradesData]) => {
        const supplierSelect = document.getElementById("supplier");
        const buyerSelect = document.getElementById("buyer");
        const carrierSelect = document.getElementById("carrier");
        const gradeSelect = document.getElementById("shipment-grade");

        // Avoid duplicating options if loadData runs more than once
        if (supplierSelect) supplierSelect.querySelectorAll("option:not([disabled])").forEach((o) => o.remove());
        if (buyerSelect) buyerSelect.querySelectorAll("option:not([disabled])").forEach((o) => o.remove());
        if (carrierSelect) carrierSelect.querySelectorAll("option:not([disabled])").forEach((o) => o.remove());
        if (gradeSelect) gradeSelect.querySelectorAll("option:not([disabled])").forEach((o) => o.remove());

        if (supplierSelect && companiesData.suppliers) {
          companiesData.suppliers.forEach((c) => {
            supplierSelect.appendChild(new Option(c.name, c.id));
          });
        }

        if (buyerSelect && companiesData.buyers) {
          companiesData.buyers.forEach((c) => {
            buyerSelect.appendChild(new Option(c.name, c.id));
          });
        }

        // Carrier is in BOL modal select#carrier
        if (carrierSelect && companiesData.hauler) {
          companiesData.hauler.forEach((c) => {
            carrierSelect.appendChild(new Option(c.name, c.id));
          });
        }

        if (gradeSelect && Array.isArray(gradesData)) {
          gradesData.forEach((g) => {
            gradeSelect.appendChild(new Option(g, g));
          });
        }
      })
      .catch((error) => {
        console.error("Error loading companies/grades:", error);
      });
  }

  function loadShipments() {
    fetch(u("api/scheduled-shipments/"))
      .then((response) => response.json())
      .then((data) => {
        if (!shipmentListContainer) return;

        shipmentListContainer.innerHTML = "";

        const now = new Date();
        const startDate = new Date();
        startDate.setDate(now.getDate() - 7);

        const endDate = new Date();
        endDate.setDate(now.getDate() + 7);

        const shipmentsByDay = {};

        // Clear calendar events
        if (calendar) calendar.getEvents().forEach((ev) => ev.remove());

        data.forEach((shipment) => {
          const dateObj = new Date(`${shipment.date}T${shipment.time}`);

          if (dateObj < startDate || dateObj > endDate) return;

          const dayOfWeek = dateObj.toLocaleDateString("en-US", {
            weekday: "long",
            timeZone: "America/Vancouver",
          });

          const fullLabel = `${shipment.date} (${dayOfWeek})`;

          if (!shipmentsByDay[fullLabel]) shipmentsByDay[fullLabel] = [];
          shipmentsByDay[fullLabel].push(shipment);

          // Add to calendar
          if (calendar) {
            calendar.addEvent({
              id: shipment.id,
              title: `${shipment.supplier} → ${shipment.buyer} (${shipment.grade})`,
              start: dateObj.toISOString(),
              allDay: false,
            });
          }
        });

        // Render list
        Object.keys(shipmentsByDay).forEach((dayLabel) => {
          const dayContainer = document.createElement("div");
          dayContainer.classList.add("shipment-day");

          const titleContainer = document.createElement("div");
          titleContainer.style.display = "flex";
          titleContainer.style.alignItems = "center";
          titleContainer.style.justifyContent = "space-between";

          const title = document.createElement("h4");
          title.textContent = dayLabel;

          const today = new Date();
          const endOfWeek = new Date();
          endOfWeek.setDate(today.getDate() + (7 - today.getDay())); // Sunday

          const allPast = shipmentsByDay[dayLabel].every((s) => {
            const t = new Date(`${s.date}T${s.time}`);
            return t < today;
          });

          const allFutureNextWeek = shipmentsByDay[dayLabel].every((s) => {
            const t = new Date(`${s.date}T${s.time}`);
            return t > endOfWeek;
          });

          if (allPast || allFutureNextWeek) {
            title.style.backgroundColor = "#999";
            title.style.color = "#fff";
          } else {
            title.style.backgroundColor = "#08666e";
            title.style.color = "#fff";
          }

          title.style.padding = "5px";
          title.style.borderRadius = "5px";

          const copyButton = document.createElement("button");
          copyButton.classList.add("copy");
          copyButton.textContent = "Copy";
          copyButton.addEventListener("click", function () {
            copyShipments(shipmentsByDay[dayLabel]);
          });

          titleContainer.appendChild(title);
          titleContainer.appendChild(copyButton);
          dayContainer.appendChild(titleContainer);

          shipmentsByDay[dayLabel].forEach((shipment) => {
            const card = document.createElement("div");
            card.className = "shipment-card";
            card.dataset.id = shipment.id;

            card.innerHTML = `
              <div class="shipment-card-left">
                <div class="shipment-date">${shipment.date} <span class="shipment-time">${shipment.time}</span></div>
                <div class="shipment-company">${shipment.supplier} → ${shipment.buyer}</div>
                <div class="shipment-grade">${shipment.grade}</div>
              </div>
              <div class="shipment-status">
                <button class="mark-done-btn status-done" data-id="${shipment.id}">✅ Complete</button>
              </div>
            `;
            dayContainer.appendChild(card);
          });

          shipmentListContainer.appendChild(dayContainer);
        });
      })
      .catch((error) => {
        console.error("Error loading shipments:", error);
      });
  }

  function copyShipments(shipments) {
    if (!shipments || shipments.length === 0) {
      alert("No shipments to copy.");
      return;
    }

    const dateObj = new Date(`${shipments[0].date}T${shipments[0].time}`);
    const dayOfWeek = dateObj.toLocaleDateString("en-US", {
      weekday: "long",
      timeZone: "America/Vancouver",
    });

    const text =
      `${dayOfWeek}:\n` +
      shipments
        .map((s) => `   - ${s.supplier} → ${s.buyer} | ${s.grade}`)
        .join("\n");

    navigator.clipboard
      .writeText(text)
      .then(() => alert("Copied."))
      .catch((err) => {
        console.error("Copy error:", err);
        alert("Copy failed.");
      });
  }

  /* =========================
     Mini calendar
     ========================= */
  const miniCalendarDays = document.getElementById("calendar-days");
  const currentMonthEl = document.getElementById("current-month");
  const prevMonthBtn = document.getElementById("prev-month");
  const nextMonthBtn = document.getElementById("next-month");

  let miniDate = new Date();

  function renderMiniCalendar() {
    if (!miniCalendarDays || !currentMonthEl) return;

    miniCalendarDays.innerHTML = "";

    const firstDay = new Date(miniDate.getFullYear(), miniDate.getMonth(), 1).getDay();
    const lastDate = new Date(miniDate.getFullYear(), miniDate.getMonth() + 1, 0).getDate();
    const today = new Date();

    currentMonthEl.textContent = miniDate.toLocaleString("default", {
      month: "long",
      year: "numeric",
    });

    for (let i = 0; i < firstDay; i++) {
      const emptyCell = document.createElement("div");
      emptyCell.classList.add("empty-day");
      miniCalendarDays.appendChild(emptyCell);
    }

    for (let d = 1; d <= lastDate; d++) {
      const dayCell = document.createElement("div");
      dayCell.textContent = d;
      dayCell.classList.add("calendar-day");

      if (
        today.getDate() === d &&
        today.getMonth() === miniDate.getMonth() &&
        today.getFullYear() === miniDate.getFullYear()
      ) {
        dayCell.classList.add("today");
      }

      dayCell.addEventListener("click", function () {
        const selectedDate = new Date(miniDate.getFullYear(), miniDate.getMonth(), d);
        if (calendar) {
          calendar.changeView("timeGridDay");
          calendar.gotoDate(selectedDate);
        }
      });

      miniCalendarDays.appendChild(dayCell);
    }
  }

  if (prevMonthBtn) {
    prevMonthBtn.addEventListener("click", function () {
      miniDate.setMonth(miniDate.getMonth() - 1);
      renderMiniCalendar();
    });
  }

  if (nextMonthBtn) {
    nextMonthBtn.addEventListener("click", function () {
      miniDate.setMonth(miniDate.getMonth() + 1);
      renderMiniCalendar();
    });
  }

  renderMiniCalendar();
});

/* =========================
   Address helpers (BOL modal)
   ========================= */
function setSupplierAddress(selectElement) {
  const selected = selectElement.options[selectElement.selectedIndex];
  const address = selected ? selected.getAttribute("data-address") : "";
  const input = document.getElementById("from-address");
  if (input) input.value = address || "";
}

function setBuyerAddress(selectElement) {
  const selected = selectElement.options[selectElement.selectedIndex];
  const address = selected ? selected.getAttribute("data-address") : "";
  const input = document.getElementById("to-address");
  if (input) input.value = address || "";
}

/* =========================
   BOL counters (BOL/LOAD)
   ========================= */
function loadDealDetails() {
  const bolForm = document.getElementById("bol-form");
  if (bolForm) bolForm.reset();

  fetch(u("api/bol-counters/"))
    .then((res) => res.json())
    .then((counter) => {
      const bolInput = document.getElementById("bol-number");
      const loadInput = document.getElementById("load-number");

      if (bolInput) bolInput.value = String(counter.bol).padStart(5, "0");
      if (loadInput) loadInput.value = String(counter.load).padStart(5, "0");
    })
    .catch((error) => {
      console.error("BOL counters error:", error);
    });
}

/* =========================
   Generate BOL PDF
   ========================= */
function generateBOLPDF() {
  const freightRadio = document.querySelector('input[name="freight"]:checked');
  const freightValue = freightRadio ? freightRadio.value : "";

  const bolData = {
    shipFrom: document.querySelector("#bolSupplier option:checked")?.text || "",
    shipFromAddress: document.getElementById("from-address")?.value || "",
    shipTo: document.querySelector("#bolBuyer option:checked")?.text || "",
    shipToAddress: document.getElementById("to-address")?.value || "",
    bolNumber: document.getElementById("bol-number")?.value || "",
    loadNumber: document.getElementById("load-number")?.value || "",
    shipDate: document.getElementById("ship-date")?.value || "",
    dueDate: document.getElementById("due-date")?.value || "",
    carrier: document.querySelector("#carrier option:checked")?.text || "",
    poNumber: document.getElementById("po-number")?.value || "",
    freightTerms: freightValue,
    commodities: [],
  };

  const rows = document.querySelectorAll("#commodity-body tr");
  rows.forEach((row) => {
    const inputs = row.querySelectorAll("input");

    // Must match row layout:
    // qty, handling, pkg, weight, hm, description, dims, class, nmfc
    bolData.commodities.push({
      qty: inputs[0]?.value || "",
      handling: inputs[1]?.value || "",
      pkg: inputs[2]?.value || "",
      weight: inputs[3]?.value || "",
      hm: inputs[4]?.value || "",
      description: inputs[5]?.value || "",
      dims: inputs[6]?.value || "",
      class: inputs[7]?.value || "",
      nmfc: inputs[8]?.value || "",
    });
  });

  fetch(u("generate-bol-pdf/"), {
    method: "POST",
    headers: csrfHeaders(),
    body: JSON.stringify(bolData),
  })
    .then((response) => response.blob())
    .then((blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `BOL_${bolData.bolNumber || "NEW"}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      // increment counters
      return fetch(u("api/bol-counters/increment/"), {
        method: "POST",
        headers: csrfHeaders(),
      });
    })
    .then(() => {
      console.log("BOL/LOAD incremented.");
    })
    .catch((err) => {
      console.error("Generate BOL PDF error:", err);
    });
}
