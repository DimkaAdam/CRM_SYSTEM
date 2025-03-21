// Открыть боковую панель для создания новой сделки
document.getElementById('addNewDealBtn').addEventListener('click', function () {
    document.getElementById('dealFormSidebar').style.width = '400px';
});

// Закрыть боковую панель для создания новой сделки
document.getElementById('closeSidebarBtn').addEventListener('click', function () {
    document.getElementById('dealFormSidebar').style.width = '0';
});

// Обработать отправку формы для новой сделки
document.getElementById('dealForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const receivedQuantityElement = document.getElementById('received_quantity');
    const buyerPriceElement = document.getElementById('buyer_price');
    const supplierPriceElement = document.getElementById('supplier_price');
    const transportCostElement = document.getElementById('transport_cost');

    if (!receivedQuantityElement || !buyerPriceElement || !supplierPriceElement || !transportCostElement) {
        console.error('Элементы формы не найдены!');
        return;
    }

    const received_quantity = parseFloat(receivedQuantityElement.value);
    const buyer_price = parseFloat(buyerPriceElement.value);
    const supplier_price = parseFloat(supplierPriceElement.value);
    const transport_cost = parseFloat(transportCostElement.value);

    // Вычисление общих сумм
    const total_amount = received_quantity * buyer_price; // Общая сумма от покупателя
    const supplier_total = received_quantity * supplier_price; // Общая сумма для поставщика
    const total_income_loss = total_amount - supplier_total - transport_cost; // Убыток/прибыль
    const supplierId = document.getElementById('supplier').value;
    const buyer = document.getElementById('buyer').value;

    const data = {
        date: document.getElementById('date').value,
        supplier: supplierId,
        buyer: buyer,
        grade: document.getElementById('grade').value,
        shipped_quantity: document.getElementById('shipped_quantity').value,
        shipped_pallets: document.getElementById('shipped_pallets').value,
        received_quantity: received_quantity,
        received_pallets: document.getElementById('received_pallets').value,
        supplier_price: supplier_price,
        buyer_price: buyer_price,
        transport_cost: transport_cost,
        transport_company: document.getElementById('transport_company').value,
        scale_ticket: document.getElementById('scale_ticket').value
    };

    fetch('http://127.0.0.1:8000/api/deals/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Deal created:', data);

        // Обновляем таблицу сделок
        const dealTable = document.getElementById('dealTable').getElementsByTagName('tbody')[0];
        const newRow = dealTable.insertRow();
        newRow.innerHTML = `
            <td>${data.date}</td>
            <td>${data.supplier_name}</td>
            <td>${data.buyer}</td>
            <td>${data.grade}</td>
            <td>${data.shipped_quantity} / ${data.shipped_pallets}</td>
            <td>${data.received_quantity} / ${data.received_pallets}</td>
            <td>${data.supplier_price}</td>
            <td>${data.supplier_total}</td>
            <td>${data.buyer_price}</td>
            <td>${data.total_amount}</td>
            <td>${data.transport_cost}</td>
            <td>${data.transport_company}</td>
            <td>${data.total_income_loss}</td>
            <td>${data.scale_ticket}</td>

        `;
        document.getElementById('dealFormSidebar').style.width = '0';
        document.getElementById('dealForm').reset();
    })
    .catch(error => console.error('Error:', error));
});

// Открыть сайдбар с деталями сделки
document.querySelectorAll('.deal-row').forEach(row => {
    row.addEventListener('click', () => {
        const dealId = row.dataset.id; // Получаем ID сделки из атрибута data-id
        fetch(`/deals/${dealId}/`) // Запрашиваем детали сделки
            .then(response => response.json())
            .then(data => {
                // Заполняем данные в сайдбар
                document.getElementById('dealDate').innerText = data.date;
                document.getElementById('dealSupplier').innerText = data.supplier;
                document.getElementById('dealBuyer').innerText = data.buyer;
                document.getElementById('dealGrade').innerText = data.grade;
                document.getElementById('dealTotalAmount').innerText = data.total_amount;

                // Сохраняем текущий ID сделки для последующих операций
                document.getElementById('viewDealSidebar').dataset.dealId = dealId;

                // Открываем сайдбар с деталями сделки
                const sidebar = document.getElementById('viewDealSidebar');
                sidebar.style.width = '400px'; // Показываем сайдбар
            })
            .catch(error => console.error('Error fetching deal details:', error));
    });
});

// Закрыть сайдбар
document.getElementById('closeViewDealSidebarBtn').addEventListener('click', () => {
    const sidebar = document.getElementById('viewDealSidebar');
    sidebar.style.width = '0'; // Закрыть сайдбар
});

// Включить режим редактирования
document.getElementById('editDealBtn').addEventListener('click', () => {
    // Скрываем детали сделки, показываем форму редактирования
    document.getElementById('dealDetailsContent').style.display = 'none';
    document.getElementById('editDealForm').style.display = 'block';

    // Заполняем форму текущими значениями
    const dealId = document.getElementById('viewDealSidebar').dataset.dealId; // Получаем ID сделки из data-атрибута

    // Делаем fetch запрос, чтобы получить данные для редактирования
    fetch(`/deals/${dealId}/`)
        .then(response => response.json())
        .then(data => {
            // Заполняем поля формы редактирования данными текущей сделки
            document.getElementById('editDate').value = data.date; // Дата
            document.getElementById('editSupplier').value = data.supplier.id; // Поставщик
            document.getElementById('editBuyer').value = data.buyer.id; // Покупатель
            document.getElementById('editGrade').value = data.grade; // Группа
            document.getElementById('editShippedQuantity').value = data.shipped_quantity; // Отправленное количество
            document.getElementById('editShippedPallets').value = data.shipped_pallets; // Отправленные паллеты
            document.getElementById('editReceivedQuantity').value = data.received_quantity; // Принятое количество
            document.getElementById('editReceivedPallets').value = data.received_pallets; // Принятые паллеты
            document.getElementById('editSupplierPrice').value = data.supplier_price; // Цена поставщика
            document.getElementById('editBuyerPrice').value = data.buyer_price; // Цена покупателя
            document.getElementById('editTransportCost').value = data.transport_cost; // Стоимость доставки
            document.getElementById('editTransportCompany').value = data.transport_company; // Транспортная компания
            document.getElementById('editScaleTicket').value = data.scale_ticket;
        })
        .catch(error => console.error('Error fetching data for editing:', error));
});

// Отключить режим редактирования
document.getElementById('cancelEditBtn').addEventListener('click', () => {
    // Показываем детали сделки, скрываем форму редактирования
    document.getElementById('dealDetailsContent').style.display = 'block';
    document.getElementById('editDealForm').style.display = 'none';
});

// Сохранение изменений
document.getElementById('editDealForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const dealId = document.getElementById('viewDealSidebar').dataset.dealId; // Получаем ID текущей сделки
    const data = {
        date: document.getElementById('editDate').value,
        supplier: document.getElementById('editSupplier').value,
        buyer: document.getElementById('editBuyer').value,
        grade: document.getElementById('editGrade').value,
        shipped_quantity: document.getElementById('editShippedQuantity').value,
        shipped_pallets: document.getElementById('editShippedPallets').value,
        received_quantity: document.getElementById('editReceivedQuantity').value,
        received_pallets: document.getElementById('editReceivedPallets').value,
        supplier_price: document.getElementById('editSupplierPrice').value,
        buyer_price: document.getElementById('editBuyerPrice').value,
        transport_cost: document.getElementById('editTransportCost').value,
        transport_company: document.getElementById('editTransportCompany').value,
        scale_ticket: document.getElementById('editScaleTicket').value,

    };

    fetch(`/deals/${dealId}/edit/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
        .then(response => response.json())
        .then(data => {
            alert('Changes saved successfully!');
            // Закрываем форму редактирования и обновляем данные в сайдбаре
            document.getElementById('dealDate').innerText = data.date;
            document.getElementById('dealSupplier').innerText = data.supplier;
            document.getElementById('dealBuyer').innerText = data.buyer;
            document.getElementById('dealGrade').innerText = data.grade;
            document.getElementById('dealTotalAmount').innerText = data.total_amount;

            document.getElementById('dealDetailsContent').style.display = 'block';
            document.getElementById('editDealForm').style.display = 'none';
        })
        .catch(error => console.error('Error saving changes:', error));
});

// Удаление сделки
document.getElementById('deleteDealBtn').addEventListener('click', () => {
    const dealId = document.getElementById('viewDealSidebar').dataset.dealId; // Получаем ID текущей сделки
    if (confirm('Are you sure you want to delete this deal?')) {
        fetch(`/deals/${dealId}/delete/`, {
            method: 'DELETE',
        })
            .then(response => {
                if (response.ok) {
                    alert('Deal deleted successfully!');
                    // Закрываем сайдбар
                    const sidebar = document.getElementById('viewDealSidebar');
                    sidebar.style.width = '0';
                    // Удаляем строку из таблицы
                    document.querySelector(`.deal-row[data-id="${dealId}"]`).remove();
                } else {
                    alert('Failed to delete deal.');
                }
            })
            .catch(error => console.error('Error deleting deal:', error));
    }
});


document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ Script loaded: Scale Ticket Sidebar");

    const scaleTicketSidebar = document.getElementById("scaleTicketSidebar");
    if (!scaleTicketSidebar) {
        console.error("⚠️ Scale Ticket Sidebar НЕ найден в DOM! Проверь ID.");
        return;
    }

    // Функция открытия сайдбара
    window.openScaleTicketSidebar = function () {
        console.log("📂 Opening Scale Ticket Sidebar...");
        if (!scaleTicketSidebar) return;

        scaleTicketSidebar.style.display = "block"; // Показываем сайдбар
        setTimeout(() => {
            scaleTicketSidebar.classList.add("open"); // Добавляем анимацию
        }, 10);
    };

    // Функция закрытия сайдбара
    window.closeScaleTicketSidebar = function () {
        console.log("📂 Closing Scale Ticket Sidebar...");
        if (!scaleTicketSidebar) return;

        scaleTicketSidebar.classList.remove("open"); // Убираем анимацию
        setTimeout(() => {
            scaleTicketSidebar.style.display = "none"; // Прячем сайдбар
        }, 300);
    };

    // Проверяем кнопку открытия
    const openBtn = document.querySelector("button[onclick='openScaleTicketSidebar()']");
    if (openBtn) {
        openBtn.addEventListener("click", openScaleTicketSidebar);
    } else {
        console.warn("⚠️ Кнопка открытия сайдбара не найдена!");
    }

    // Проверяем кнопку закрытия
    const closeBtn = document.querySelector("#scaleTicketSidebar .close-btn");
    if (closeBtn) {
        closeBtn.addEventListener("click", closeScaleTicketSidebar);
    } else {
        console.warn("⚠️ Кнопка закрытия сайдбара не найдена!");
    }
});

// 📌 Функция для загрузки данных по Scale Ticket Number
document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ Script loaded: Scale Ticket Export");

    function setCurrentTime() {
        const now = new Date();
        const formattedTime = now.toLocaleTimeString('en-US', { hour12: false }).slice(0, 5);
        const timeInput = document.getElementById("deal_time");
        if (timeInput) {
            timeInput.value = formattedTime;
        } else {
            console.warn("⚠️ Поле 'time' не найдено в DOM.");
        }
    }

    setCurrentTime();

    window.fetchDealData = function () {
        let ticketNumberElement = document.getElementById("ticket_number");
        if (!ticketNumberElement) {
            console.error("🚨 Ошибка: поле 'ticket_number' не найдено!");
            return;
        }
        let ticketNumber = ticketNumberElement.value;

        if (!ticketNumber || ticketNumber.length < 3) {
            console.warn("⚠️ Введите минимум 3 символа для поиска сделки.");
            return;
        }

        console.log(`🔍 Fetching deal data for ticket: ${ticketNumber}`);

        fetch(`/get-deal-by-ticket/?ticket_number=${ticketNumber}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server responded with ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    console.log("✅ Deal found:", data.deal);

                    const setValueIfExists = (id, value) => {
                        const element = document.getElementById(id);
                        if (element) {
                            element.value = value;
                        } else {
                            console.warn(`⚠️ Поле '${id}' не найдено в DOM.`);
                        }
                    };

                    setValueIfExists("selectedDealId", data.deal.id);
                    setValueIfExists("scaleticket_date", data.deal.date);
                    setValueIfExists("scaleticket_received_quantity", data.deal.received_quantity);
                    setValueIfExists("pallets", data.deal.received_pallets);
                    setValueIfExists("supplier_name", data.deal.supplier_name);
                    setValueIfExists("scaleticket_grade", data.deal.grade);

                    // 🏋️‍♂️ Генерируем tare_weight в диапазоне 5170-5470 кг
                    let randomTareWeight = 5170 + Math.floor(Math.random() * 301);
                    setValueIfExists("tare_weight", randomTareWeight);

                    // 📌 Получаем net_weight (либо из сделки, либо считаем по received_quantity)
                    let netWeight = parseFloat(data.deal.net_weight_str || data.deal.received_quantity * 1000 || 0);
                    setValueIfExists("net_weight", netWeight);

                    // 📌 Пересчитываем Gross Weight = Tare Weight + Net Weight
                    let grossWeight = randomTareWeight + netWeight;
                    setValueIfExists("gross_weight", grossWeight);

                    console.log(`📌 Пересчет весов: Tare = ${randomTareWeight}, Net = ${netWeight}, Gross = ${grossWeight}`);
                } else {
                    console.warn("❌ Deal not found for this Scale Ticket.");
                    alert("Deal not found for this Scale Ticket.");
                }
            })
            .catch(error => console.error("🚨 Error fetching deal data:", error));
    };

    window.exportScaleTicket = function (event) {
        event.preventDefault();

        const getValueOrWarn = (id, defaultValue = "") => {
            const element = document.getElementById(id);
            if (!element) {
                console.warn(`⚠️ Поле '${id}' не найдено в DOM.`);
                return defaultValue;
            }
            return element.value || defaultValue;
        };

        let ticketNumber = getValueOrWarn("ticket_number");
        if (!ticketNumber) {
            alert("⚠️ Please enter a scale ticket number before exporting.");
            return;
        }

        let dealTime = getValueOrWarn("deal_time", "N/A");
        let licencePlate = getValueOrWarn("licence_plate", "N/A");
        let tareWeight = parseFloat(getValueOrWarn("tare_weight", "0"));
        let netWeight = parseFloat(getValueOrWarn("net_weight", "0"));

        // 🔄 Пересчитываем Gross перед отправкой
        let grossWeight = tareWeight + netWeight;

        console.log(`📂 Exporting Scale Ticket: ${ticketNumber}, Time: ${dealTime}, Licence: ${licencePlate}, Gross: ${grossWeight}, Tare: ${tareWeight}, Net: ${netWeight}`);

        let url = `/export-scale-ticket/?ticket_number=${ticketNumber}`
                + `&time=${encodeURIComponent(dealTime)}`
                + `&licence_plate=${encodeURIComponent(licencePlate)}`
                + `&gross_weight=${encodeURIComponent(grossWeight)}`
                + `&tare_weight=${encodeURIComponent(tareWeight)}`
                + `&net_weight=${encodeURIComponent(netWeight)}`;

        window.open(url, '_blank');
    };

    const exportBtn = document.getElementById("exportScaleTicketBtn");
    if (exportBtn) {
        exportBtn.addEventListener("click", exportScaleTicket);
        console.log("✅ Export button connected.");
    } else {
        console.error("🚨 Export button NOT FOUND! Проверь ID: exportScaleTicketBtn");
    }

    const licencePlates = ['SY1341', 'WB3291', '153'];
    const licenceSelect = document.getElementById("licence_plate");

    if (licenceSelect) {
        console.log("🔹 Заполняем список номеров...");

        const placeholderOption = document.createElement("option");
        placeholderOption.value = "";
        placeholderOption.textContent = "Select Licence Plate";
        placeholderOption.disabled = true;
        placeholderOption.selected = true;
        licenceSelect.appendChild(placeholderOption);

        licencePlates.forEach(plate => {
            const option = document.createElement("option");
            option.value = plate;
            option.textContent = plate;
            licenceSelect.appendChild(option);
        });

        console.log("✅ Licence plate dropdown filled.");
    } else {
        console.error("🚨 Licence plate dropdown (licence_plate) NOT FOUND!");
    }
});