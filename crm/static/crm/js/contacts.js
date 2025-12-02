
// Open Add Client Sidebar
document.getElementById('addContactBtn').addEventListener('click', function () {
    document.getElementById('addClientSidebar').style.width = '300px';
    document.getElementById('cancelBtn').style.display = 'inline';
});

// Cancel Add Client
document.getElementById('cancelBtn').addEventListener('click', function () {
    document.getElementById('addClientSidebar').style.width = '0';
    document.getElementById('cancelBtn').style.display = 'none';
    document.getElementById('clientForm').reset();
});

// Close Add Client Sidebar
document.getElementById('closeSidebarBtn').addEventListener('click', function () {
    document.getElementById('addClientSidebar').style.width = '0';
    document.getElementById('cancelBtn').style.display = 'none';
});

// Handle Add Client Form Submission
document.getElementById('clientForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const company = document.getElementById('company').value;
    const clientType = document.getElementById('clientType').value;

    fetch('/api/clients/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}',
        },
        body: JSON.stringify({
            name: name,
            email: email,
            phone: phone,
            company: company,
            client_type: clientType,
        }),
    })
        .then(response => response.json())
        .then(data => {
            if (data) {
                const clientTable = document.getElementById('clientTable').getElementsByTagName('tbody')[0];
                const newRow = clientTable.insertRow();
                newRow.innerHTML = `
                    <td>${data.name}<br><span>${data.email}</span><br><span>${data.phone || 'Not provided'}</span></td>
                    <td>No deals <button class="add-deal-btn">Add deal</button></td>
                    <td>${data.company}</td>
                    <td>${data.created}</td>
                    <td>${data.client_type || 'Not specified'}</td>
                `;

                document.getElementById('addClientSidebar').style.width = '0';
                document.getElementById('cancelBtn').style.display = 'none';
                document.getElementById('clientForm').reset();
            }
        })
        .catch(error => {
            alert('Failed to add contact. Please try again.');
            console.error('Error:', error);
        });
});

// Filter Clients by Type
document.getElementById('categorySelect').addEventListener('change', function () {
    const selectedValue = this.value;
    const rows = document.querySelectorAll('#clientTable tbody tr');

    rows.forEach(row => {
        const clientType = row.children[4].textContent.toLowerCase();
        if (selectedValue === 'all' || clientType === selectedValue) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
});

// Open View Client Sidebar
document.querySelectorAll('.client-row').forEach(row => {
    row.addEventListener('click', function () {
        const clientId = this.getAttribute('data-id');
        const sidebar = document.getElementById('viewClientSidebar');
        const content = document.getElementById('clientDetailsContent');

        fetch(`http://127.0.0.1:8000/api/clients/${clientId}/`)
            .then(response => response.json())
            .then(data => {
                content.innerHTML = `
                    <div class="client-details-container">
                        <p><strong><img src="${iconPath}" alt="Logo" class="logo-img"> </strong> ${data.name}</p>
                    </div>
                    <div class="client-details-container">
                       <p><strong><img src="${iconPath_3}" alt="Logo" class="logo-img"> </strong> ${data.email}</p>
                    </div>
                    <div class="client-details-container">
                        <p><strong><img src="${iconPath_1}" alt="Logo" class="logo-img"> </strong> ${data.phone || 'Not provided'}</p>
                    </div>
                    <div class="client-details-container">
                        <p><strong><img src="${iconPath_2}" alt="Logo" class="logo-img"> </strong> ${data.company}</p>
                    </div>
                    <div class="client-details-container">
                        <p><strong><img src="${iconPath_4}" alt="Logo" class="logo-img"> </strong> ${data.client_type || 'Not specified'}</p>
                    </div>
                    <div class="client-details-container">
                        <p><strong>Created:</strong> ${data.created}</p>
                    </div>
                `;
                sidebar.style.width = '300px';
            })
            .catch(error => {
                console.error('Error fetching client data:', error);
                content.innerHTML = '<p>Error loading client details.</p>';
            });
    });
});

// Close View Client Sidebar
document.getElementById('closeViewSidebarBtn').addEventListener('click', function () {
    document.getElementById('viewClientSidebar').style.width = '0';
});