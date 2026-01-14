document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('generate-bol-btn').addEventListener('click', function() {
    const modal = document.getElementById('bol-modal');
    modal.style.display = 'block';

    // ⏳ Проверяем, что поля появились
    const checkFieldsReady = setInterval(() => {
        const bolInput = document.getElementById('bol-number');
        const loadInput = document.getElementById('load-number');

        if (bolInput && loadInput) {
            clearInterval(checkFieldsReady);
            console.log("✅ Поля BOL и LOAD готовы в DOM");
            loadDealDetails();
        }
    }, 50); // Проверяем каждые 50 мс
});

// ✅ место для toggle календаря:
    const toggleBtn = document.getElementById("toggle-calendar-btn");
    const calendarWrapper = document.getElementById("calendar-wrapper");

    toggleBtn.addEventListener("click", function () {
        if (calendarWrapper.style.display === "none" || calendarWrapper.style.display === "") {
            calendarWrapper.style.display = "block";
            toggleBtn.textContent = "Hide Calendar";
        } else {
            calendarWrapper.style.display = "none";
            toggleBtn.textContent = "Open Calendar";
        }
    });
document.addEventListener('click', function (e) {
    if (e.target && e.target.id === 'add-commodity') {
        const tbody = document.getElementById('commodity-body');
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input type="number" name="qty[]" required></td>
            <td><input type="text" name="pkg[]" required></td>
            <td><input type="number" name="weight[]" required></td>
            <td><input type="text" name="description[]" required></td>
            <td><input type="text" name="dims[]"></td>
            <td><input type="text" name="class[]"></td>
            <td><input type="text" name="nmfc[]"></td>
            <td><button type="button" class="remove-commodity">🗑</button></td>
        `;
        tbody.appendChild(row);
    }

    if (e.target && e.target.classList.contains('remove-commodity')) {
        e.target.closest('tr').remove();
    }
    if (e.target && e.target.classList.contains("mark-done-btn")) {
        const shipmentId = e.target.dataset.id;

        fetch(`/api/scheduled-shipments/done/${shipmentId}/`, {
            method: "POST"
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "done") {
                alert("✅ Shipment marked as done!");
                loadShipments();  // Перезагрузим список
            } else {
                alert("❌ Failed to mark as done.");
            }
        })
        .catch(err => {
            console.error("❌ Error:", err);
            alert("❌ Server error");
        });
    }
});

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
            fetch(u("api/companies-by-type/").then(res => res.json()),  // ✅ заменили clients на companies-by-type
            fetch("/api/grades/").then(res => res.json())
        ])
        .then(([companiesData, gradesData]) => {
            let supplierSelect = document.getElementById("supplier");
            let buyerSelect = document.getElementById("buyer");
            let carrierSelect = document.getElementById("carrier");  // ✅ добавлено
            let gradeSelect = document.getElementById("shipment-grade");

            companiesData.suppliers.forEach(client => {
                supplierSelect.appendChild(new Option(client.name, client.id));
            });

            companiesData.buyers.forEach(client => {
                buyerSelect.appendChild(new Option(client.name, client.id));
            });

            // ✅ теперь также заполняем carrier, если такой элемент есть
            if (carrierSelect) {
                companiesData.hauler.forEach(client => {
                    carrierSelect.appendChild(new Option(client.name, client.id));
                });
            }

            gradesData.forEach(grade => {
                gradeSelect.appendChild(new Option(grade, grade));
            });
        })
        .catch(error => console.error("🚨 Error loading companies/grades:", error));
    }


    loadData();

    // 📌 Загрузка отгрузок
    function loadShipments() {
    fetch("/api/scheduled-shipments/")
        .then(response => response.json())
        .then(data => {
            let shipmentListContainer = document.getElementById("shipment-list");
            shipmentListContainer.innerHTML = "";  // ✅ Очищаем перед обновлением

            let now = new Date();
            let startDate = new Date();
            startDate.setDate(now.getDate() - 7);  // ✅ Показать за неделю назад
            let endDate = new Date();
            endDate.setDate(now.getDate() + 7);    // ✅ Показать на неделю вперёд

            let shipmentsByDay = {};  // 🛠️ Добавь, иначе ошибка

            calendar.getEvents().forEach(event => event.remove());  // ✅ Удаляем старые события

            data.forEach(shipment => {
                let date = new Date(`${shipment.date}T${shipment.time}`);

                // ✅ Пропускаем всё вне диапазона [-7; +7]
                if (date < startDate || date > endDate) {
                    return;
                }

                let dayOfWeek = date.toLocaleDateString("en-US", {
                    weekday: "long",
                    timeZone: "America/Vancouver"
                });
                let fullLabel = date.toISOString().split("T")[0] + ` (${dayOfWeek})`;

                if (!shipmentsByDay[fullLabel]) {
                    shipmentsByDay[fullLabel] = [];
                }
                shipmentsByDay[fullLabel].push(shipment);

                // ✅ Добавляем в FullCalendar
                calendar.addEvent({
                    id: shipment.id,
                    title: `${shipment.supplier} → ${shipment.buyer} (${shipment.grade})`,
                    start: date.toISOString(),
                    allDay: false
                });
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

                    // ✅ Проверим: все ли отгрузки прошли
                    let today = new Date();
                    let endOfWeek = new Date();
                    endOfWeek.setDate(today.getDate() + (7 - today.getDay())); // воскресенье текущей недели

                    let allPast = shipmentsByDay[day].every(shipment => {
                        let shipmentTime = new Date(`${shipment.date}T${shipment.time}`);
                        return shipmentTime < today;
                    });

                    let allFutureNextWeek = shipmentsByDay[day].every(shipment => {
                        let shipmentTime = new Date(`${shipment.date}T${shipment.time}`);
                        return shipmentTime > endOfWeek;
                    });

                    if (allPast || allFutureNextWeek) {
                        title.style.backgroundColor = "#999";  // серый
                        title.style.color = "#fff";
                    } else {
                        title.style.backgroundColor = "#08666e";  // тёмно-зелёный для текущей недели (включая сегодня)
                        title.style.color = "#fff";
                    }

                    title.style.padding = "5px";
                    title.style.borderRadius = "5px";
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

                    shipmentsByDay[day].forEach(shipment => {
                      const card = document.createElement("div");
                      card.className = "shipment-card";
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
            .catch(error => console.error("🚨 Error loading shipments:", error));
    }

        function copyShipments(shipments, button) {
            if (!shipments || shipments.length === 0) {
                alert("❌ No shipments to copy.");
                return;
            }

            let date = new Date(`${shipments[0].date}T${shipments[0].time}`);
            let dayOfWeek = date.toLocaleDateString("en-US", { weekday: "long", timeZone: "America/Vancouver" });

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
        let isRecurring = document.getElementById("is_recurring").checked;
        let recurrenceType = document.getElementById("recurrence_type").value;

        if (!supplier || !buyer || !date || !time || !grade) {
            alert("❌ Please fill in all fields!");
            return;
        }

        let shipmentData = {
            supplier: supplier,
            buyer: buyer,
            datetime: `${date}T${time}:00`,
            grade: grade,
            is_recurring: isRecurring,
            recurrence_type: recurrenceType,
            recurrence_day: new Date(date).getDay()  // 🆕 день недели от 0 (вс) до 6 (сб)
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

    // Закрытие модального окна
    document.getElementById('close-bol-modal').addEventListener('click', function() {
        document.getElementById('bol-modal').style.display = 'none';
    });

    // Автоматическое подтягивание адреса при выборе компании
    document.getElementById('bolSupplier').addEventListener('change', function() {
        document.getElementById('from-address').value = this.options[this.selectedIndex].dataset.address;

    });

    // Генерация PDF BOL
    document.getElementById('bol-form').addEventListener('submit', function(event) {
        event.preventDefault();
        generateBOLPDF();
    });
});



document.addEventListener('click', function (e) {
    if (e.target.classList.contains('remove-commodity')) {
        e.target.closest('tr').remove();
    }
});

// 📌 Выбор Supplier → подставляем адрес отправителя
function setSupplierAddress(selectElement) {
    const selected = selectElement.options[selectElement.selectedIndex];
    const address = selected.getAttribute('data-address');
    document.getElementById('from-address').value = address || '';
}

// 📌 Выбор Buyer → подставляем адрес получателя
function setBuyerAddress(selectElement) {
    const selected = selectElement.options[selectElement.selectedIndex];
    const address = selected.getAttribute('data-address');
    document.getElementById('to-address').value = address || '';
}

// ✅ Загрузка данных сделки (используется при открытии модалки)

function loadDealDetails() {
    console.log("✅ loadDealDetails вызвана");

    // 🧹 Очистим форму, если нужно
    document.getElementById('bol-form').reset();

    // 🧾 Загружаем auto-инкремент BOL и LOAD
    fetch('/api/bol-counters/')
        .then(res => res.json())
        .then(counter => {
            const bolInput = document.getElementById('bol-number');
            const loadInput = document.getElementById('load-number');

            if (bolInput) {
                bolInput.value = `${String(counter.bol).padStart(5, '0')}`;
                console.log("🧪 Установлен BOL:", bolInput.value);
            } else {
                console.warn("⚠️ bol-number input not found in DOM!");
            }

            if (loadInput) {
                loadInput.value = `${String(counter.load).padStart(5, '0')}`;
                console.log("🧪 Установлен LOAD:", loadInput.value);
            } else {
                console.warn("⚠️ load-number input not found in DOM!");
            }
        })
        .catch(error => {
            console.error("❌ Ошибка получения номеров BOL/LOAD:", error);
        });
}


// Получаем выбранную сделку из таблицы
function getSelectedDealId() {
    let selectedDeal = document.querySelector('.deal-selected');
    return selectedDeal ? selectedDeal.dataset.dealId : null;
}

// Генерация PDF
function generateBOLPDF() {
    let bolData = {
        shipFrom: document.querySelector('#bolSupplier option:checked')?.text || '',
        shipFromAddress: document.getElementById('from-address').value,
        shipTo: document.querySelector('#bolBuyer option:checked')?.text || '',
        shipToAddress: document.getElementById('to-address').value,
        bolNumber: document.getElementById('bol-number').value,
        loadNumber: document.getElementById('load-number').value,
        shipDate: document.getElementById('ship-date').value,
        dueDate: document.getElementById('due-date').value,
        carrier: document.querySelector('#carrier option:checked')?.text || '',
        poNumber: document.getElementById('po-number').value,
        freightTerms: document.querySelector('input[name="freight"]:checked').value,
        commodities:[]
    };

    // 🔁 Собираем данные из всех строк commodities
    const rows = document.querySelectorAll('#commodity-body tr');
    rows.forEach(row => {
        const cells = row.querySelectorAll('input');
        bolData.commodities.push({
            qty: cells[0]?.value || '',
            handling: cells[1]?.value || '',
            pkg: cells[2]?.value || '',
            weight: cells[3]?.value || '',
            hm: cells[4]?.value || '',
            description: cells[5]?.value || '',
            dims: cells[6]?.value || '',
            class: cells[7]?.value || '',
            nmfc: cells[8]?.value || ''
        });
    });

    fetch('/generate-bol-pdf/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
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

        // 🔁 Инкремент
        return fetch('/api/bol-counters/increment/', {
            method: 'POST'
        });
    })
    .then(() => {
        console.log('✅ BOL и LOAD номера увеличены');
    })
    .catch(err => {
        console.error("❌ Ошибка при генерации PDF или инкременте номеров:", err);
    });
}