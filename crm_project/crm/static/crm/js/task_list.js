document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: "/api/events/",
        editable: true,
        selectable: true,
        nowIndicator: true,
    });

    calendar.render();

    // 📌 Загружаем список поставщиков, покупателей и грейдов ОДНИМ ЗАПРОСОМ
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

    // 📌 Загружаем список отгрузок и добавляем их в календарь
    function loadShipments() {
        fetch("/api/shipments/")
            .then(response => response.json())
            .then(data => {
                let shipmentListContainer = document.getElementById("shipment-list");
                shipmentListContainer.innerHTML = ""; // Очищаем перед обновлением

                let shipmentsByDay = {}; // Объект для группировки по дням недели
                let today = new Date();
                let nextWeek = new Date();
                nextWeek.setDate(today.getDate() + 7); // 📌 Ограничение в 7 дней

                // 📌 Очищаем старые события перед добавлением новых
                calendar.getEvents().forEach(event => event.remove());

                data.forEach(shipment => {
                    let date = new Date(`${shipment.date}T${shipment.time}:00Z`); // 📌 Принудительно в UTC
                    let dayOfWeek = date.toLocaleDateString("en-US", { weekday: "long", timeZone: "UTC" }); // 📌 Указываем "UTC"

                    if (date >= today && date <= nextWeek) { // 📌 Фильтруем по 7 дням
                        if (!shipmentsByDay[dayOfWeek]) {
                            shipmentsByDay[dayOfWeek] = [];
                        }

                        shipmentsByDay[dayOfWeek].push(shipment);

                        // 📌 Добавляем отгрузку в FullCalendar
                        calendar.addEvent({
                            title: `${shipment.supplier} → ${shipment.buyer} (${shipment.grade})`,
                            start: date.toISOString(), // 📌 Используем точное время UTC
                            allDay: false
                        });
                    }
                });

                // 📌 Создаем блоки по дням недели
                Object.keys(shipmentsByDay).forEach(day => {
                    let dayContainer = document.createElement("div");
                    dayContainer.classList.add("shipment-day");

                    let title = document.createElement("h4");
                    title.textContent = day;
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
                                <tr>
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


    loadShipments(); // ✅ Загружаем отгрузки сразу при загрузке страницы

    // 📌 Обработчик формы добавления отгрузки
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

        fetch("/api/shipments/add/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(shipmentData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                alert("✅ Shipment added!");

                // 📌 Добавляем новую отгрузку в FullCalendar
                calendar.addEvent({
                    title: `${document.getElementById("supplier").selectedOptions[0].text} → ${document.getElementById("buyer").selectedOptions[0].text} (${grade})`,
                    start: `${date}T${time}`,
                    allDay: false
                });

                loadShipments(); // ✅ Обновляем список отгрузок
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
