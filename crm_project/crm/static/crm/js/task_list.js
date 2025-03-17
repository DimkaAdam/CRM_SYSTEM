document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: function(fetchInfo, successCallback, failureCallback) {
            fetch("/api/events/")
                .then(response => response.json())
                .then(events => {
                    console.log("📌 События загружены:", events);
                    successCallback(events);
                })
                .catch(error => {
                    console.error("❌ Ошибка загрузки событий:", error);
                    failureCallback(error);
                });
        },
        editable: true,
        selectable: true,
        nowIndicator: true,

        dateClick: function(info) {
            let title = prompt("Введите название события:");
            if (!title) return;

            let startTime = prompt("Введите время начала (HH:MM, 24h формат):", "10:00");
            if (!startTime || !/^\d{2}:\d{2}$/.test(startTime)) {
                alert("❌ Некорректный формат времени. Используйте HH:MM (например, 09:30).");
                return;
            }

            let [hours, minutes] = startTime.split(":").map(Number);
            let fullDateTime = new Date(info.date);
            fullDateTime.setHours(hours, minutes, 0);

            console.log("📩 Отправляем запрос:", fullDateTime.toISOString());

            fetch("/api/events/add/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: title,
                    start: fullDateTime.toISOString(),
                    allDay: false
                })
            }).then(response => response.json())
              .then(data => {
                  console.log("📌 Ответ сервера:", data);
                  if (data.status === "success") {
                      calendar.refetchEvents(); // ✅ Пробуем обновить события

                      // ❗ Если `refetchEvents()` не сработал, добавляем событие вручную
                      calendar.addEvent({
                          id: data.event.id,  // ❗ ВАЖНО: добавь ID, если сервер его возвращает
                          title: data.event.title,
                          start: data.event.start,
                          allDay: false
                      });
                  } else {
                      alert("❌ Ошибка при добавлении события");
                  }
              });

        },

        eventClick: function(info) {
            if (confirm("Удалить событие?")) {
                fetch(`/api/events/delete/${info.event.id}/`, {
                    method: "DELETE"
                }).then(response => response.json())
                  .then(data => {
                      console.log("📌 Удаление события:", data);
                      if (data.status === "deleted") {
                          info.event.remove();
                      }
                  });
            }
        }
    });

    calendar.render(); // ✅ Исправленная ошибка

    // 🎯 Мини-календарь
    const calendarDays = document.getElementById("calendar-days");
    const currentMonth = document.getElementById("current-month");
    const prevMonthBtn = document.getElementById("prev-month");
    const nextMonthBtn = document.getElementById("next-month");

    let date = new Date();

    function renderCalendar() {
        calendarDays.innerHTML = "";
        let firstDay = new Date(date.getFullYear(), date.getMonth(), 1).getDay();
        let lastDate = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
        let today = new Date();

        currentMonth.textContent = date.toLocaleString("default", { month: "long", year: "numeric" });

        for (let i = 0; i < firstDay; i++) {
            let emptyCell = document.createElement("div");
            emptyCell.classList.add("empty-day");
            calendarDays.appendChild(emptyCell);
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

            calendarDays.appendChild(dayCell);
        }
    }

    prevMonthBtn.addEventListener("click", function () {
        date.setMonth(date.getMonth() - 1);
        renderCalendar();
    });

    nextMonthBtn.addEventListener("click", function () {
        date.setMonth(date.getMonth() + 1);
        renderCalendar();
    });

    renderCalendar();
});
