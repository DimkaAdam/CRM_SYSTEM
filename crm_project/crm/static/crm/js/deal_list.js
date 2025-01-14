
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
        transport_company: document.getElementById('transport_company').value
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
        `;
        document.getElementById('dealFormSidebar').style.width = '0';
        document.getElementById('dealForm').reset();
    })
    .catch(error => console.error('Error:', error));
});

// Открыть боковую панель для просмотра сделки
document.querySelectorAll('.deal-row').forEach(row => {
    row.addEventListener('click', function () {
        const dealId = this.getAttribute('data-id');
        const sidebar = document.getElementById('viewDealSidebar');
        const content = document.getElementById('dealDetailsContent');
        const deleteButton = document.getElementById('deleteDealBtn');

        fetch(`http://127.0.0.1:8000/api/deals/${dealId}/`)
            .then(response => response.json())
            .then(data => {
                content.innerHTML = `
                    <div class="deal-details-container">
                        <p><strong>Date:</strong> ${data.date}</p>
                        <p><strong>Supplier:</strong> ${data.supplier}</p>
                        <p><strong>Buyer:</strong> ${data.buyer}</p>
                        <p><strong>Grade:</strong> ${data.grade}</p>
                        <p><strong>Shipped Quantity:</strong> ${data.shipped_quantity}</p>
                        <p><strong>Received Quantity:</strong> ${data.received_quantity}</p>
                        <p><strong>Supplier Price:</strong> ${data.supplier_price}</p>
                        <p><strong>Buyer Price:</strong> ${data.buyer_price}</p>
                        <p><strong>Total Amount:</strong> ${data.total_amount}</p>
                        <p><strong>Transport Cost:</strong> ${data.transport_cost}</p>
                        <p><strong>Transport Company:</strong> ${data.transport_company}</p>
                    </div>
                `;
                deleteButton.style.display = 'inline-block';

                deleteButton.onclick = function () {
                    if (confirm('Are you sure you want to delete this deal?')) {
                        fetch(`http://127.0.0.1:8000/api/deals/${dealId}/`, {
                            method: 'DELETE',
                            headers: {
                                'X-CSRFToken': '{{ csrf_token }}',
                            },
                        })
                        .then(response => {
                            if (response.ok) {
                                document.querySelector(`.deal-row[data-id="${dealId}"]`).remove();
                                sidebar.style.width = '0';
                                alert('Deal deleted successfully');
                            } else {
                                alert('Failed to delete deal. Please try again.');
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('An error occurred while deleting the deal.');
                        });
                    }
                };
                sidebar.style.width = '400px';
            })
            .catch(error => {
                console.error('Error fetching deal data:', error);
                content.innerHTML = '<p>Error loading deal details.</p>';
            });
    });
});

// Закрыть боковую панель для просмотра сделки
document.getElementById('closeViewDealSidebarBtn').addEventListener('click', function () {
    document.getElementById('viewDealSidebar').style.width = '0';
});