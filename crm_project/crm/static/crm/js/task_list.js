document.addEventListener('DOMContentLoaded', function () {
    // 🔹 Инициализация основного календаря
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: "/api/scheduled-shipments/",  // ✅ Загружаем только запланированные отгрузки
        editable: true,
        selectable: true,
        nowIndicator: true,
        eventClick: function (info) {
            if (confirm("❌ Do you really want to delete this shipment?")) {
                let shipmentId = info.event.id;

                fetch(`/api/scheduled-shipments/delete/${shipmentId}/`, {
                    method: "DELETE"
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === "deleted") {
                        info.event.remove();
                        removeShipmentFromList(shipmentId);
                        alert("✅ Shipment deleted successfully!");
                    } else {
                        alert("❌ Error deleting shipment.");
                    }
                })
                .catch(error => {
                    console.error("🚨 Error deleting shipment:", error);
                    alert("❌ Server error");
                });
            }
        }
    });

    calendar.render();  // ✅ Запускаем FullCalendar

    // 📌 Удаление отгрузки из списка
    function removeShipmentFromList(shipmentId) {
        let shipmentRows = document.querySelectorAll(`#shipment-list tr[data-id="${shipmentId}"]`);
        shipmentRows.forEach(row => row.remove());
    }

    // 📌 Загрузка списка поставщиков, покупателей и грейдов
    function loadData() {
        Promise.all([
            fetch("/api/clients/").then(res => res.json()),
            fetch("/api/grades/").then(res => res.json())
        ])
        .then(([clientsData, gradesData]) => {
            let supplierSelect = document.getElementById("supplier");
            let buyerSelect = document.getElementById("buyer");
            let gradeSelect = document.getElementById("shipment-grade");

            clientsData.suppliers.forEach(client => {
                supplierSelect.appendChild(new Option(client.name, client.id));
            });

            clientsData.buyers.forEach(client => {
                buyerSelect.appendChild(new Option(client.name, client.id));
            });

            gradesData.forEach(grade => {
                gradeSelect.appendChild(new Option(grade, grade));
            });
        })
        .catch(error => console.error("🚨 Error loading clients/grades:", error));
    }

    loadData();

    // 📌 Загрузка отгрузок (только запланированные)
    function loadShipments() {
        fetch("/api/scheduled-shipments/")
            .then(response => response.json())
            .then(data => {
                let shipmentListContainer = document.getElementById("shipment-list");
                shipmentListContainer.innerHTML = "";  // ✅ Очищаем перед обновлением

                let shipmentsByDay = {};
                let today = new Date();
                let nextWeek = new Date();
                nextWeek.setDate(today.getDate() + 7);

                calendar.getEvents().forEach(event => event.remove());  // ✅ Удаляем старые события

                data.forEach(shipment => {
                    let date = new Date(`${shipment.date}T${shipment.time}:00Z`);
                    let dayOfWeek = date.toLocaleDateString("en-US", { weekday: "long", timeZone: "UTC" });

                    if (date >= today && date <= nextWeek) {
                        if (!shipmentsByDay[dayOfWeek]) {
                            shipmentsByDay[dayOfWeek] = [];
                        }
                        shipmentsByDay[dayOfWeek].push(shipment);

                        // ✅ Добавляем в FullCalendar
                        calendar.addEvent({
                            id: shipment.id,
                            title: `${shipment.supplier} → ${shipment.buyer} (${shipment.grade})`,
                            start: date.toISOString(),
                            allDay: false
                        });
                    }
                });

               // ✅ Отображаем список по дням недели
                Object.keys(shipmentsByDay).forEach(day => {
                    let dayContainer = document.createElement("div");
                    dayContainer.classList.add("shipment-day");

                    let titleContainer = document.createElement("div");
                    titleContainer.style.display = "flex";
                    titleContainer.style.alignItems = "center";
                    titleContainer.style.justifyContent = "space-between";

                    let title = document.createElement("h4");
                    title.textContent = day;
                    title.style.backgroundColor = "#007aff";
                    title.style.color = "white";
                    title.style.padding = "5px";
                    title.style.borderRadius = "5px";

                    // ✅ Добавляем кнопку копирования (динамически)
                    let copyButton = document.createElement("button");
                    copyButton.classList.add("copy");
                    copyButton.innerHTML = `
                        <span data-text-end="Copied!" data-text-initial="Copy to clipboard" class="tooltip"></span>
                        <span>
                            <svg xml:space="preserve" style="enable-background:new 0 0 512 512" viewBox="0 0 6.35 6.35" height="20" width="20" class="clipboard">
                                <g><path fill="currentColor" d="M2.43.265c-.3 0-.548.236-.573.53h-.328a.74.74 0 0 0-.735.734v3.822a.74.74 0 0 0 .735.734H4.82a.74.74 0 0 0 .735-.734V1.529a.74.74 0 0 0-.735-.735h-.328a.58.58 0 0 0-.573-.53zm0 .529h1.49c.032 0 .049.017.049.049v.431c0 .032-.017.049-.049.049H2.43c-.032 0-.05-.017-.05-.049V.843c0-.032.018-.05.05-.05zm-.901.53h.328c.026.292.274.528.573.528h1.49a.58.58 0 0 0 .573-.529h.328a.2.2 0 0 1 .206.206v3.822a.2.2 0 0 1-.206.205H1.53a.2.2 0 0 1-.206-.205V1.529a.2.2 0 0 1 .206-.206z"></path></g>
                            </svg>
                            <svg xml:space="preserve" style="enable-background:new 0 0 512 512" viewBox="0 0 24 24" height="18" width="18" class="checkmark">
                                <g><path fill="currentColor" d="M9.707 19.121a.997.997 0 0 1-1.414 0l-5.646-5.647a1.5 1.5 0 0 1 0-2.121l.707-.707a1.5 1.5 0 0 1 2.121 0L9 14.171l9.525-9.525a1.5 1.5 0 0 1 2.121 0l.707.707a1.5 1.5 0 0 1 0 2.121z"></path></g>
                            </svg>
                        </span>
                    `;

                    copyButton.addEventListener("click", function () {
                        copyShipments(shipmentsByDay[day], copyButton);
                    });

                    titleContainer.appendChild(title);
                    titleContainer.appendChild(copyButton);
                    dayContainer.appendChild(titleContainer);

                    let table = document.createElement("table");
                    table.classList.add("shipment-table");
                    table.innerHTML = `
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Time</th>
                                <th>Supplier</th>
                                <th>Buyer</th>
                                <th>Grade</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${shipmentsByDay[day].map(shipment => `
                                <tr data-id="${shipment.id}">
                                    <td>${shipment.date}</td>
                                    <td>${shipment.time}</td>
                                    <td>${shipment.supplier}</td>
                                    <td>${shipment.buyer}</td>
                                    <td>${shipment.grade}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    `;
                    dayContainer.appendChild(table);
                    shipmentListContainer.appendChild(dayContainer);
                });
            })
            .catch(error => console.error("🚨 Error loading shipments:", error));
    }

        function copyShipments(shipments, button) {
            if (!shipments || shipments.length === 0) {
                alert("❌ No shipments to copy.");
                return;
            }

            let date = new Date(`${shipments[0].date}T${shipments[0].time}:00Z`);
            let dayOfWeek = date.toLocaleDateString("en-US", { weekday: "long", timeZone: "UTC" });

            let text = `${dayOfWeek}:\n` + shipments.map(shipment =>
                `   - ${shipment.supplier} → ${shipment.buyer} | ${shipment.grade}`
            ).join("\n");

            navigator.clipboard.writeText(text).then(() => {
                let tooltip = button.querySelector(".tooltip");
                tooltip.textContent = "Copied!";
                setTimeout(() => { tooltip.textContent = "Copy to clipboard"; }, 2000);
            }).catch(err => {
                console.error("❌ Error copying:", err);
                alert("❌ Failed to copy shipments");
            });
        }

    loadShipments(); // ✅ Загружаем отгрузки только один раз

     // 📌 Функция отрисовки мини-календаря
    function renderMiniCalendar() {
        const miniCalendarDays = document.getElementById("calendar-days");
        const currentMonth = document.getElementById("current-month");
        miniCalendarDays.innerHTML = ""; // Очищаем календарь

        let firstDay = new Date(date.getFullYear(), date.getMonth(), 1).getDay();
        let lastDate = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
        let today = new Date();

        currentMonth.textContent = date.toLocaleString("default", { month: "long", year: "numeric" });

        for (let i = 0; i < firstDay; i++) {
            let emptyCell = document.createElement("div");
            emptyCell.classList.add("empty-day");
            miniCalendarDays.appendChild(emptyCell);
        }

        for (let i = 1; i <= lastDate; i++) {
            let dayCell = document.createElement("div");
            dayCell.textContent = i;
            dayCell.classList.add("calendar-day");

            if (today.getDate() === i && today.getMonth() === date.getMonth() && today.getFullYear() === date.getFullYear()) {
                dayCell.classList.add("today");
            }

            dayCell.addEventListener("click", function () {
                let selectedDate = new Date(date.getFullYear(), date.getMonth(), i);
                calendar.changeView('timeGridDay');
                calendar.gotoDate(selectedDate);
            });

            miniCalendarDays.appendChild(dayCell);
        }
    }

    // 📌 Обработчики переключения месяцев в мини-календаре
    const prevMonthBtn = document.getElementById("prev-month");
    const nextMonthBtn = document.getElementById("next-month");

    prevMonthBtn.addEventListener("click", function () {
        date.setMonth(date.getMonth() - 1);
        renderMiniCalendar();
    });

    nextMonthBtn.addEventListener("click", function () {
        date.setMonth(date.getMonth() + 1);
        renderMiniCalendar();
    });

    let date = new Date();
    renderMiniCalendar();  // ✅ Инициализация мини-календаря


    // 📌 Форма добавления отгрузки
    document.getElementById("add-shipment-form").addEventListener("submit", function (e) {
        e.preventDefault();

        let supplier = document.getElementById("supplier").value;
        let buyer = document.getElementById("buyer").value;
        let date = document.getElementById("shipment-date").value;
        let time = document.getElementById("shipment-time").value;
        let grade = document.getElementById("shipment-grade").value;

        if (!supplier || !buyer || !date || !time || !grade) {
            alert("❌ Please fill in all fields!");
            return;
        }

        let shipmentData = {
            supplier: supplier,
            buyer: buyer,
            datetime: `${date}T${time}:00`,
            grade: grade
        };

        fetch("/api/scheduled-shipments/add/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(shipmentData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                alert("✅ Shipment added!");
                loadShipments();  // ✅ Обновляем список после добавления
            } else {
                alert("❌ Error adding shipment");
            }
        })
        .catch(error => {
            console.error("Error adding shipment:", error);
            alert("❌ Server error");
        });
    });
});


document.getElementById('generate-bol-btn').addEventListener('click', function() {
    document.getElementById('bol-modal').style.display = 'block';
    loadDealDetails();
});

// Закрытие модального окна
document.getElementById('close-bol-modal').addEventListener('click', function() {
    document.getElementById('bol-modal').style.display = 'none';
});

// Автоматическое подтягивание адреса при выборе компании
document.getElementById('ship-to-company').addEventListener('change', function() {
    document.getElementById('ship-to-address').value = this.options[this.selectedIndex].dataset.address;
});

// Загружаем данные из сделок, как в deal_list.js
function loadDealDetails() {
    let selectedDealId = getSelectedDealId();
    if (!selectedDealId) {
        alert("❌ Выберите сделку перед генерацией BOL!");
        return;
    }

    fetch(`/deals/${selectedDealId}/`)  // ✅ Используем API сделок
        .then(res => res.json())
        .then(data => {
            let selectCompany = document.getElementById('ship-to-company');
            selectCompany.innerHTML = `<option value="${data.buyer_id}" selected>${data.buyer}</option>`;
            document.getElementById('ship-to-address').value = data.buyer_address || "";
            document.getElementById('carrier').innerHTML = `<option value="${data.transport_company}" selected>${data.transport_company}</option>`;
            document.getElementById('bol-number').value = `BOL-${selectedDealId}`;
            document.getElementById('load-number').value = `LOAD-${selectedDealId}`;
            document.getElementById('ship-date').value = data.date;
            document.getElementById('po-number').value = data.scale_ticket || "";
        })
        .catch(error => console.error('❌ Ошибка загрузки сделки:', error));
}

// Получаем ID выбранной сделки
function getSelectedDealId() {
    let selectedDeal = document.querySelector('.deal-selected');
    return selectedDeal ? selectedDeal.dataset.dealId : null;
}

// Генерация PDF BOL
document.getElementById('bol-form').addEventListener('submit', function(event) {
    event.preventDefault();
    generateBOLPDF();
});

function generateBOLPDF() {
    let bolData = {
        shipTo: document.getElementById('ship-to-company').value,
        shipToAddress: document.getElementById('ship-to-address').value,
        bolNumber: document.getElementById('bol-number').value,
        loadNumber: document.getElementById('load-number').value,
        shipDate: document.getElementById('ship-date').value,
        dueDate: document.getElementById('due-date').value,
        carrier: document.getElementById('carrier').value,
        poNumber: document.getElementById('po-number').value,
        freightTerms: document.querySelector('input[name="freight"]:checked').value
    };

    fetch('/generate-bol-pdf/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token }}' },
        body: JSON.stringify(bolData)
    })
    .then(response => response.blob())
    .then(blob => {
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement('a');
        a.href = url;
        a.download = `BOL_${bolData.bolNumber}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });
}

