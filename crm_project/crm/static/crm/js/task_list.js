
document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth', // Вид календаря
        height: 400, // Уменьшаем высоту
        contentHeight: 300, // Высота контента
        events: [
            {% for event in events %}
            {
                title: "{{ event.summary }}",
                start: "{{ event.start.dateTime|default:event.start.date }}",
                allDay: true
            },
            {% endfor %}
        ]
    });
    calendar.render();
});

