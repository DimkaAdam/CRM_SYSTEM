document.addEventListener("DOMContentLoaded", function () {                         // ⏳ Ждём загрузку DOM
  // =========================
  // ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
  // =========================
  const TOP_SUPPLIERS = 12;                                                        // 🔢 Сколько поставщиков показывать на бар-чарте

  const fmtMoney = (v) => {                                                        // 💵 Формат валюты с разделителями
    const n = Number(v ?? 0);
    return n.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 2 });
  };

  const fmtNumber = (v) => Number(v ?? 0).toLocaleString();                        // 🔢 Разделители для чисел

  const hexWithAlpha = (hex, alpha = 0.2) => {                                     // 🎨 Добавляем прозрачность к HEX
    if (hex.startsWith("#") && hex.length === 7) {
      const a = Math.round(alpha * 255).toString(16).padStart(2, "0");
      return `${hex}${a}`;
    }
    return hex;                                                                    // Если пришёл не HEX — вернём как есть
  };

  const metricColors = {                                                           // 🎯 Цвета по метрикам (единый словарь)
    profit: "#4CAF50",
    pallets: "#2196F3",
    hauler: "#FF9800",
    suppliers: "#9C27B0",
    total_tonnage: "#E91E63",
    occ11_tonnage: "#3F51B5",
    plastic_tonnage: "#00BCD4",
    mixed_tonnage: "#CDDC39",
    sales: "#F44336"
  };

  // =========================
  // БАР-ЧАРТ: ДОХОД/УБЫТОК ПО ПОСТАВЩИКАМ
  // =========================
  if (document.getElementById("salesChart")) {                                     // ✅ Есть ли canvas для бар-чарта
    const suppliersIncome = window.suppliersIncome;                                 // 🔗 Ожидаем объект: { "Supplier A": 1234, ... }

    if (!suppliersIncome || Object.keys(suppliersIncome).length === 0) {           // 🛑 Нет данных
      console.error("No data available for sales analytics");
      alert("No data available for sales analytics.");
    } else {
      // 👉 Сортируем по значению и берём топ-N
      const sortedEntries = Object.entries(suppliersIncome)                         // [[name, value], ...]
        .sort((a, b) => b[1] - a[1])                                               // По убыванию дохода
        .slice(0, TOP_SUPPLIERS);                                                  // Берём нужное количество

      const salesLabels = sortedEntries.map(([name]) => name);                     // 🏷️ Метки (имена)
      const salesData = sortedEntries.map(([, val]) => Number(val));               // 📊 Значения (числа)

      const salesCtx = document.getElementById("salesChart").getContext("2d");     // 🎨 Контекст canvas

      const getBarFill = (val, ctx) => {                                           // 🌈 Градиент столбца по значению
        const g = ctx.createLinearGradient(0, 0, 0, 300);                          // Вертикальный градиент
        if (val < 0) {                                                             // 🔻 Отрицательные значения — красные
          g.addColorStop(0, "#FF5252");
          g.addColorStop(1, "#C62828");
        } else if (val >= 3500) {                                                  // 🥇 Большой доход — тёплый жёлтый
          g.addColorStop(0, "#FFF176");
          g.addColorStop(1, "#FBC02D");
        } else if (val >= 2000) {                                                  // 🟣 Средний — розово-фиолетовый
          g.addColorStop(0, "#FF80AB");
          g.addColorStop(1, "#AB47BC");
        } else {                                                                   // 🔵 Малый — фиолетово-синий
          g.addColorStop(0, "#9575CD");
          g.addColorStop(1, "#5E35B1");
        }
        return g;
      };

      const barFills = salesData.map(v => getBarFill(v, salesCtx));                // 🎨 Заполняем цвета для каждого бара

      // Подбираем максимум оси Y с запасом
      const maxAbs = Math.max(...salesData.map(v => Math.abs(v))) || 1;            // Максимум по модулю
      const suggestedMax = Math.ceil(maxAbs * 1.2 / 100) * 100;                    // Округлим вверх с 20% запасом

      // Инициализируем график
      new Chart(salesCtx, {
        type: "bar",
        data: {
          labels: salesLabels,                                                      // Имена поставщиков
          datasets: [{
            label: "Income/Loss",                                                   // Лейбл набора
            data: salesData,                                                        // Значения
            backgroundColor: barFills,                                              // Градиенты
            borderColor: barFills,                                                  // Границы теми же цветами
            borderWidth: 1,                                                         // Толщина границы
            borderRadius: 6,                                                        // Скругления столбцов
            barThickness: "flex"                                                    // Адаптивная ширина
          }]
        },
        options: {
          responsive: true,                                                         // Адаптивность
          maintainAspectRatio: false,                                               // Свободная высота контейнера
          plugins: {
            legend: { display: false },                                             // Легенда не нужна
            tooltip: { callbacks: { label: ctx => `${fmtMoney(ctx.parsed.y)}` } }   // Подсказки в $
          },
          scales: {
            x: {
              ticks: { autoSkip: false, maxRotation: 45, minRotation: 0 }           // Читабельные подписи
            },
            y: {
              beginAtZero: true,                                                    // Начинаем с нуля
              suggestedMax,                                                         // Предложенный максимум
              ticks: { callback: (v) => fmtMoney(v) },                              // Формат оси Y в $
              grid: { drawBorder: false }                                           // Аккуратная сетка
            }
          }
        }
      });
    }
  }

  // =========================
  // ЛАЙН-ЧАРТ: МЕСЯЧНЫЕ МЕТРИКИ («червячок»)
  // =========================
  if (document.getElementById("monthlyWormChart")) {                               // ✅ Есть ли canvas для линейного графика
    const chartData = window.chartData || {};                                      // 🔗 Ожидаем { months: [...], profit: [...], ... }
    const months = Array.isArray(chartData.months) ? chartData.months : [];        // 📆 Месяцы
    const metric = "profit";                                                        // 📍 Метрика по умолчанию

    if (months.length === 0 || !Array.isArray(chartData[metric])) {                // 🛑 Нет корректных данных
      console.warn("No monthly chart data");
      return;
    }

    const monthlyCtx = document.getElementById("monthlyWormChart").getContext("2d");// 🎨 Контекст canvas

    const baseColor = metricColors[metric] || "#888";                               // 🎯 Базовый цвет линии
    const grad = monthlyCtx.createLinearGradient(0, 0, 0, 240);                     // 🌈 Вертикальный градиент
    grad.addColorStop(0, hexWithAlpha(baseColor, 0.35));                            // Полупрозрачный верх
    grad.addColorStop(1, hexWithAlpha(baseColor, 0.00));                            // Прозрачный низ

    const dataPairs = months.map((m, i) => ({ x: m, y: Number(chartData[metric][i] ?? 0) })); // 📊 Пары (месяц, значение)

    // Создаём график
    window.monthlyChart = new Chart(monthlyCtx, {
      type: "line",
      data: {
        labels: months.map(String),                                                 // Подписи оси X
        datasets: [{
          label: "PROFIT",                                                          // Лейбл набора
          data: dataPairs.map(p => p.y),                                            // Массив значений
          borderColor: baseColor,                                                   // Цвет линии
          backgroundColor: grad,                                                    // Градиент под линией
          fill: true,                                                               // Включаем заливку
          borderWidth: 3,                                                           // Толщина линии
          pointRadius: 0,                                                           // Точки скрыты
          tension: 0.35                                                             // Сглаживание («червячок»)
        }]
      },
      options: {
        responsive: true,                                                           // Адаптивность
        maintainAspectRatio: false,                                                 // Свободная высота
        plugins: {
          legend: { display: false },                                               // Легенду убираем
          tooltip: { callbacks: { label: ctx => fmtMoney(ctx.parsed.y) } }          // Подсказки в $
        },
        scales: {
          x: { grid: { display: false } },                                          // Без вертикальной сетки
          y: {
            beginAtZero: true,                                                      // От нуля
            ticks: { callback: (v) => fmtMoney(v) },                                // Формат оси Y
            grid: { drawBorder: false }                                             // Аккуратная сетка
          }
        }
      }
    });

    // ========= Переключение метрики =========
    window.updateMonthlyChart = function (metricKey) {                              // 🔄 Смена метрики по кнопкам/дропдауну
      if (!window.monthlyChart || !chartData[metricKey]) return;                    // Если данных нет — выходим

      const color = metricColors[metricKey] || "#666";                              // Новый цвет
      const values = months.map((_, i) => Number(chartData[metricKey][i] ?? 0));    // Новые значения
      const grad2 = monthlyCtx.createLinearGradient(0, 0, 0, 240);                  // Новый градиент
      grad2.addColorStop(0, hexWithAlpha(color, 0.35));                             // Полупрозрачный верх
      grad2.addColorStop(1, hexWithAlpha(color, 0.00));                             // Прозрачный низ

      const ds = window.monthlyChart.data.datasets[0];                              // Датасет графика
      ds.data = values;                                                             // Подменяем данные
      ds.label = metricKey.replace(/_/g, " ").toUpperCase();                        // Обновляем лейбл
      ds.borderColor = color;                                                       // Цвет линии
      ds.backgroundColor = grad2;                                                   // Заливка

      window.monthlyChart.update();                                                 // Ререндер

      const last = values.length ? values[values.length - 1] : 0;                   // Текущее значение (последнее)
      const currentDisplay = document.getElementById("currentMetricDisplay");        // DOM-элемент с текущим значением
      if (currentDisplay) {                                                         // Если есть, обновим
        currentDisplay.textContent = fmtMoney(last);
        currentDisplay.style.backgroundColor = hexWithAlpha(color, 0.12);
        currentDisplay.style.color = color;
      }
    };
  }
});
