document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',  // Вид календаря (месячный)
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: JSON.parse('{{ events|safe }}'),  // ✅ Загружаем события из Django
        editable: false,
        selectable: true,
        nowIndicator: true
    });

    calendar.render();
});
