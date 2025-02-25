document.addEventListener("DOMContentLoaded", function () {
  // График по поставщикам (bar chart)
  if (document.getElementById('salesChart')) {
    const suppliersIncome = window.suppliersIncome;
    if (!suppliersIncome || Object.keys(suppliersIncome).length === 0) {
      console.error('No data available for sales analytics');
      alert('No data available for sales analytics.');
    }
    const salesLabels = Object.keys(suppliersIncome);
    const salesData = Object.values(suppliersIncome);
    var salesCtx = document.getElementById('salesChart').getContext('2d');
    new Chart(salesCtx, {
      type: 'bar',
      data: {
        labels: salesLabels,
        datasets: [{
          label: 'Income/Loss',
          data: salesData,
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          borderColor: 'rgba(75, 192, 192, 1)',
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

  // График по месяцам (line chart)
  if (document.getElementById('monthlyChart')) {
    const chartData = window.chartData;
    var monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
    window.monthlyChart = new Chart(monthlyCtx, {
      type: 'line',
      data: {
        labels: chartData.months.map(m => `Month ${m}`),
        datasets: [{
          label: 'Profit',
          data: chartData.profit,
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 2
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

    // Глобальная функция для переключения метрик
    window.updateMonthlyChart = function (metric) {
      if (window.monthlyChart && window.chartData) {
        window.monthlyChart.data.datasets[0].data = window.chartData[metric];
        window.monthlyChart.data.datasets[0].label = metric.replace('_', ' ').toUpperCase();
        window.monthlyChart.update();
      }
    }
  }
});

document.addEventListener("DOMContentLoaded", function() {
  // Предположим, что window.chartData содержит данные, например:
  // { profit: [100, 120, 130, ...], pallets: [10, 12, 15, ...], ... }

  // Определим объект с цветами для каждой метрики
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

  // Функция обновления графика и текущего показателя
  window.updateMonthlyChart = function(metric) {
      if (window.monthlyChart && window.chartData) {
        window.monthlyChart.data.datasets[0].data = window.chartData[metric];
        window.monthlyChart.data.datasets[0].label = metric.replace('_', ' ').toUpperCase();

        // Обновляем цвета графика:
        window.monthlyChart.data.datasets[0].backgroundColor = hoverColors[metric] + "33"; // прозрачный фон
        window.monthlyChart.data.datasets[0].borderColor = hoverColors[metric];

        window.monthlyChart.update();

        // Обновляем текущий показатель
        const dataArray = window.chartData[metric];
        const currentValue = dataArray && dataArray.length ? dataArray[dataArray.length - 1] : 0;
        const currentDisplay = document.getElementById('currentMetricDisplay');
        if (currentDisplay) {
          currentDisplay.innerText = currentValue;
          currentDisplay.style.backgroundColor = hoverColors[metric] || '#888';
        }
      }
    }
});
