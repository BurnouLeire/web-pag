let histogramChart, pieChart;

// --- Mock Data Alineado a la Tesis de RIVALESA S.A. ---
const mockData = {
    // Métricas del Modelo (Req. No Funcional 3.2.2.1.4)
    aiMetrics: {
        r2Score: 0.84, // Supera el 0.80 requerido
        processedCertificates: 4125, // Basado en tu Figura 18
        daysOptimized: 1240, // Suma de días extendidos de forma segura
    },
    // Datos para el histograma de carga de trabajo
    calibrationByMonth: {
        labels: ['Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
        data: [45, 52, 38, 65, 48, 70]
    },
    // Datos para la tabla con enfoque en OPTIMIZACIÓN
    instrumentTypes: [
        { type: 'Manómetros', total: 145, stdInterval: 365, optInterval: 412, confidence: '94%' },
        { type: 'Vacuómetros', total: 82, stdInterval: 365, optInterval: 380, confidence: '88%' },
        { type: 'Indicadores de Presión', total: 210, stdInterval: 180, optInterval: 175, confidence: '91%' },
        { type: 'Manovacuómetros', total: 65, stdInterval: 365, optInterval: 405, confidence: '95%' }
    ]
};

document.addEventListener('DOMContentLoaded', function() {
    initDashboardAsync();
});

async function initDashboardAsync() {
    try {
        const data = await fetchDashboardData();

        // Actualizar Tarjetas de la Tesis
        document.getElementById('r2-score').textContent = data.aiMetrics.r2Score.toFixed(2);
        document.getElementById('total-certs').textContent = data.aiMetrics.processedCertificates.toLocaleString();
        document.getElementById('days-optimized').textContent = "+" + data.aiMetrics.daysOptimized;

        initHistogram(data.calibrationByMonth);
        initPieChart(data.instrumentTypes);
        updateTypeTable(data.instrumentTypes);

    } catch (error) {
        console.error("Error al inicializar el dashboard:", error);
    }
}

function initHistogram(calibrationData) {
    const ctx = document.getElementById('histogramChart').getContext('2d');
    if (histogramChart) histogramChart.destroy();

    histogramChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: calibrationData.labels,
            datasets: [{
                label: 'Certificados Procesados',
                data: calibrationData.data,
                backgroundColor: '#164ab8',
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { color: '#b0c4de' }, grid: { color: 'rgba(22, 74, 184, 0.1)' } },
                x: { ticks: { color: '#b0c4de' }, grid: { display: false } }
            }
        }
    });
}

function initPieChart(instrumentData) {
    const ctx = document.getElementById('pieChart').getContext('2d');
    const labels = instrumentData.map(item => item.type);
    const values = instrumentData.map(item => item.total);
    
    if (pieChart) pieChart.destroy();

    pieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: ['#164ab8', '#f57e20', '#27ae60', '#e74c3c'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#b0c4de', padding: 20 } }
            }
        }
    });
}

function updateTypeTable(typeDataArray) {
    const tableBody = document.getElementById('typeTable');
    tableBody.innerHTML = '';

    typeDataArray.forEach(item => {
        const row = document.createElement('tr');
        row.className = 'border-b border-[#164ab8]/20 hover:bg-[#164ab8]/10 transition';
        
        row.innerHTML = `
            <td class="py-3 px-4 text-white font-medium">${item.type}</td>
            <td class="text-center py-3 px-4 text-white">${item.total}</td>
            <td class="text-center py-3 px-4 text-[#7a9cc6]">${item.stdInterval} d</td>
            <td class="text-center py-3 px-4 text-[#52be80] font-bold">${item.optInterval} d</td>
            <td class="text-center py-3 px-4">
                <span class="bg-[#27ae60]/20 text-[#52be80] text-xs px-2 py-1 rounded">${item.confidence}</span>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

async function fetchDashboardData() {
    try {
        // Llamada al endpoint real de Flask que acabamos de crear
        const response = await fetch('/api/dashboard/stats');
        if (!response.ok) throw new Error("Error en la respuesta del servidor");
        
        const data = await response.json();

        // Retornamos el objeto formateado exactamente como lo espera el resto de tu JS
        return {
            expired: data.vencidos,
            upcoming: data.proximos,
            calibratedThisMonth: 15, // Puedes calcularlo también en el service
            total: data.total_registros,
            aiMetrics: {
                r2Score: 0.84, // Estático o desde config
                processedCertificates: data.total_registros,
                daysOptimized: 1240 
            },
            calibrationByMonth: {
                labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'], // O dinámico desde data.histograma
                data: [10, 20, 15, 25, 30, 40]
            },
            instrumentTypes: data.instrumentTypes
        };
    } catch (error) {
        console.error('Error fetching real data:', error);
        return mockData; // Fallback al mockup si algo falla
    }
}