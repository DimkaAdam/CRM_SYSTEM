document.addEventListener("DOMContentLoaded", function () {
  // ========= График по поставщикам (Bar Chart) =========
  if (document.getElementById('salesChart')) {
    const suppliersIncome = window.suppliersIncome;
    if (!suppliersIncome || Object.keys(suppliersIncome).length === 0) {
      console.error('No data available for sales analytics');
      alert('No data available for sales analytics.');
    } else {
      const salesLabels = Object.keys(suppliersIncome);   // Например, ["Supplier A", "Supplier B", ...]
      const salesData = Object.values(suppliersIncome);   // Например, [10000, 30000, ...]

      const salesCtx = document.getElementById('salesChart').getContext('2d');

      // Функция для генерации градиента в зависимости от значения
      const getGradient = (value, ctx) => {
        const gradient = ctx.createLinearGradient(0, 0, 0, 200);
        if (value >= 3500) {
          gradient.addColorStop(0, '#fffa4d'); // Желтый
        } else if (value >= 2000) {
          gradient.addColorStop(0, '#ff5468'); // Фиолетовый
        } else {
          gradient.addColorStop(0, '#8543dd'); // Синий
        }
        gradient.addColorStop(1, '#4b35ac'); // Белый цвет в конце градиента

        return gradient;
      };

      const barColors = salesData.map(value => getGradient(value, salesCtx)); // Генерация градиентов для каждого значения

      new Chart(salesCtx, {
        type: 'bar',
        data: {
          labels: salesLabels,
          datasets: [{
            label: 'Income/Loss',
            data: salesData,
            backgroundColor: barColors, // Использование сгенерированных градиентов
            borderColor: barColors,     // Используем такие же цвета для границ
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    }
  }

  // ========= Объект цветов для месячных метрик =========
  const hoverColors = {
    profit: '#4CAF50',
    pallets: '#2196F3',
    hauler: '#FF9800',
    suppliers: '#9C27B0',
    total_tonnage: '#E91E63',
    occ11_tonnage: '#3F51B5',
    plastic_tonnage: '#00BCD4',
    mixed_tonnage: '#CDDC39',
    sales: '#F44336'
  };

  // ========= График по месяцам (Line Chart – "червячок") =========
  if (document.getElementById('monthlyWormChart')) {
    const chartData = window.chartData;
    const monthlyCtx = document.getElementById('monthlyWormChart').getContext('2d');

    // Формируем массив объектов для графика: [{ x: 'Jan', y: chartData.profit[0] }, ...]
    const wormData = chartData.months.map((month, idx) => ({
      x: month,
      y: chartData.profit[idx]
    }));

    // Создаём линейный градиент для базовой заливки/линии
    const gradient = monthlyCtx.createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, '#ff0000');   // красный (верх)
    gradient.addColorStop(0.5, '#ffff00');   // желтый (середина)
    gradient.addColorStop(1, '#8a2be2');   // фиолетовый (низ)

    window.monthlyChart = new Chart(monthlyCtx, {
      type: 'line',
      data: {
        labels: chartData.months.map(m => `Month ${m}`),
        datasets: [{
          label: 'Profit',
          data: wormData,
          parsing: {
            xAxisKey: 'x',
            yAxisKey: 'y'
          },
          borderColor: gradient,
          backgroundColor: gradient,
          fill: false,
          borderWidth: 5,
          pointRadius: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: 'category',
            ticks: { color: '#333', font: { size: 14 } }
          },
          y: {
            beginAtZero: true,
            ticks: { color: '#333', font: { size: 14 } }
          }
        }
      }
    });

    // ========= Функция переключения метрик для месячного графика =========
    window.updateMonthlyChart = function (metric) {
      if (window.monthlyChart && window.chartData) {
        const newData = chartData.months.map((month, idx) => ({
          x: month,
          y: chartData[metric][idx]
        }));
        window.monthlyChart.data.datasets[0].data = newData;
        window.monthlyChart.data.datasets[0].label = metric.replace('_', ' ').toUpperCase();

        const color = hoverColors[metric] || '#888';
        window.monthlyChart.data.datasets[0].borderColor = color;
        window.monthlyChart.data.datasets[0].backgroundColor = color + '33'; // добавляем прозрачность

        window.monthlyChart.update();

        const dataArray = chartData[metric];
        const currentValue = dataArray && dataArray.length ? dataArray[dataArray.length - 1] : 0;
        const currentDisplay = document.getElementById('currentMetricDisplay');
        if (currentDisplay) {
          currentDisplay.innerText = currentValue;
          currentDisplay.style.backgroundColor = color;
        }
      }
    };
  }
});
