// Глобальные функции открытия и закрытия сайдбара Scale Ticket
window.openScaleTicketSidebar = function () {
    console.log("📂 Opening Scale Ticket Sidebar...");
    const sidebar = document.getElementById("scaleTicketSidebar");
    if (!sidebar) {
        console.error("⚠️ Scale Ticket Sidebar НЕ найден в DOM!");
        return;
    }
    sidebar.style.display = "block";
    setTimeout(() => {
        sidebar.classList.add("open");
    }, 10);
};

window.closeScaleTicketSidebar = function () {
    console.log("📂 Closing Scale Ticket Sidebar...");
    const sidebar = document.getElementById("scaleTicketSidebar");
    if (!sidebar) return;
    sidebar.classList.remove("open");
    setTimeout(() => {
        sidebar.style.display = "none";
    }, 300);
};

// Функция загрузки данных по Scale Ticket Number
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
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("✅ Deal found:", data.deal);

                document.getElementById("selectedDealId").value = data.deal.id;
                document.getElementById("scaleticket_date").value = data.deal.date;
                document.getElementById("scaleticket_received_quantity").value = data.deal.received_quantity;
                document.getElementById("pallets").value = data.deal.received_pallets;
                document.getElementById("supplier_name").value = data.deal.supplier_name;
                document.getElementById("scaleticket_grade").value = data.deal.grade;

                // 🏋️‍♂️ Генерируем случайный tare_weight
                let tareWeight = 5170 + Math.floor(Math.random() * 301);
                document.getElementById("tare_weight").value = tareWeight;

                // 📌 Рассчитываем net_weight (если отсутствует, считаем по received_quantity)
                let netWeight = parseFloat(data.deal.net_weight_str || data.deal.received_quantity * 1000 || 0);
                document.getElementById("scaleticket_received_quantity").value = netWeight / 1000; // В тоннах

                // 📌 Рассчитываем Gross Weight = Tare Weight + Net Weight
                let grossWeight = tareWeight + netWeight;
                document.getElementById("gross_weight").value = grossWeight;

                console.log(`📌 Пересчет весов: Tare = ${tareWeight}, Net = ${netWeight}, Gross = ${grossWeight}`);
            } else {
                console.warn("❌ Deal not found for this Scale Ticket.");
                alert("Deal not found for this Scale Ticket.");
            }
        })
        .catch(error => console.error("🚨 Error fetching deal data:", error));
};




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
        scale_ticket: document.getElementById("ticket_number").value
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
                document.getElementById('dealScaleTicket').innerText = data.total_amount;
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
    const exportButton = document.getElementById("exportScaleTicketBtn");
    if (exportButton) {
        exportButton.addEventListener("click", function(event) {
            event.preventDefault();
            exportScaleTicket(event);
        });

        // Добавляем анимацию при клике
        exportButton.addEventListener("mousedown", function () {
            exportButton.classList.add("clicked");
        });

        exportButton.addEventListener("mouseup", function () {
            setTimeout(() => {
                exportButton.classList.remove("clicked");
            }, 200);
        });

        console.log("✅ Export PDF button connected.");
    } else {
        console.error("❌ Export PDF button NOT FOUND!");
    }
});
