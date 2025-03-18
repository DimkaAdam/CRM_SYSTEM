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

                    let title = document.createElement("h4");
                    title.textContent = day;
                    title.style.backgroundColor = "#007aff";
                    title.style.color = "white";
                    title.style.padding = "5px";
                    title.style.borderRadius = "5px";
                    dayContainer.appendChild(title);

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

    loadShipments();  // ✅ Загружаем отгрузки только один раз

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
