
document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',  // Недельный вид
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: "/api/events/",  // Загружаем события
        editable: true,
        selectable: true,
        nowIndicator: true,

        // Добавление событий при клике
        dateClick: function(info) {
            let title = prompt("Введите название события:");
            if (title) {
                fetch("/api/events/add/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        title: title,
                        start: info.dateStr,
                        allDay: true
                    })
                }).then(response => response.json())
                  .then(data => {
                      if (data.status === "success") {
                          calendar.refetchEvents();
                      } else {
                          alert("Ошибка при добавлении события");
                      }
                  });
            }
        },

        // Удаление события при клике
        eventClick: function(info) {
            if (confirm("Удалить событие?")) {
                fetch(`/api/events/delete/${info.event.id}/`, {
                    method: "DELETE"
                }).then(response => response.json())
                  .then(data => {
                      if (data.status === "deleted") {
                          info.event.remove();
                      } else {
                          alert("Ошибка удаления");
                      }
                  });
            }
        }
    });

    calendar.render();

    // Мини-календарь (jQuery UI Datepicker)
    $("#mini-calendar").datepicker({
        onSelect: function(dateText) {
            let date = new Date(dateText);
            calendar.changeView('timeGridWeek');  // Переключаемся на неделю
            calendar.gotoDate(date);  // Переход на выбранную дату
        }
    });
});
