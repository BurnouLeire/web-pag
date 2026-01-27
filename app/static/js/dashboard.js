let histogramChart, pieChart;
let allHistoricalData = {};

// <--- CAMBIO IMPORTANTE: Cambié el nombre a 'v2_ml' para borrar la memoria vieja
// y obligar al navegador a traer los datos nuevos del modelo .pkl
const CACHE_KEY = 'dashboard_data_v2_ml'; 

// Mock Data de respaldo
const mockData = {
    aiMetrics: { r2Score: 0.94, processedCertificates: 0 }, 
    historicalData: { 2024: [0,0,0,0,0,0,0,0,0,0,0,0] },
    availableYears: [2024],
    instrumentTypes: []
};

document.addEventListener('DOMContentLoaded', function() {
    initDashboardAsync();
});

async function initDashboardAsync() {
    try {
        let data;

        // <--- Lógica de Caché
        const cachedData = sessionStorage.getItem(CACHE_KEY);

        if (cachedData) {
            console.log("📦 Usando datos en caché (sin petición al servidor)");
            data = JSON.parse(cachedData);
        } else {
            console.log("🌐 No hay caché, descargando datos del modelo ML...");
            data = await fetchDashboardData();

            // Guardamos solo si no hay error
            if (data && !data.error) {
                sessionStorage.setItem(CACHE_KEY, JSON.stringify(data));
            }
        }

        // 1. KPIs (Ya sin los "Días Optimizados")
        if (data.aiMetrics) {
            const elR2 = document.getElementById('r2-score');
            const elCerts = document.getElementById('total-certs');
            
            // Aquí mostramos el R2 que viene de tu archivo .pkl
            if(elR2) elR2.textContent = data.aiMetrics.r2Score;
            
            // Total de certificados procesados
            if(elCerts) elCerts.textContent = data.aiMetrics.processedCertificates.toLocaleString();
        }

        // 2. Histograma
        if (data.historicalData && data.availableYears) {
            allHistoricalData = data.historicalData;
            setupYearSelector(data.availableYears);
            
            const latestYear = Math.max(...data.availableYears);
            initHistogram(latestYear);
        }

        // 3. Gráfico de Dona y Tabla
        if (data.instrumentTypes && data.instrumentTypes.length > 0) {
            initPieChart(data.instrumentTypes);
            updateTypeTable(data.instrumentTypes);
        } else {
            console.warn("No hay tipos de instrumentos para mostrar.");
        }

    } catch (error) {
        console.error("Error init:", error);
    }
}

async function fetchDashboardData() {
    try {
        const response = await fetch('/dashboard/data');
        if (!response.ok) throw new Error("Error HTTP " + response.status);
        const jsonData = await response.json();
        if (jsonData.error) throw new Error(jsonData.error);
        return jsonData;
    } catch (error) {
        console.warn("Usando fallback por error:", error);
        return mockData;
    }
}

// --- GRÁFICOS ---

function setupYearSelector(years) {
    const selector = document.getElementById('yearFilter');
    if(!selector) return;
    selector.innerHTML = '';
    
    years.sort((a, b) => b - a).forEach(year => {
        const opt = document.createElement('option');
        opt.value = year;
        opt.textContent = `Año ${year}`;
        selector.appendChild(opt);
    });

    selector.addEventListener('change', (e) => updateHistogramData(e.target.value));
}

function initHistogram(year) {
    const ctx = document.getElementById('histogramChart')?.getContext('2d');
    if (!ctx) return;

    if (histogramChart) histogramChart.destroy();

    const dataValues = allHistoricalData[year] || Array(12).fill(0);

    histogramChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
            datasets: [{
                label: 'Calibraciones',
                data: dataValues,
                backgroundColor: '#164ab8',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { borderDash: [2, 4] } },
                x: { grid: { display: false } }
            }
        }
    });
}

function updateHistogramData(year) {
    if (!histogramChart) return;
    histogramChart.data.datasets[0].data = allHistoricalData[year] || Array(12).fill(0);
    histogramChart.update();
}

function initPieChart(dataArray) {
    const ctx = document.getElementById('pieChart')?.getContext('2d');
    if (!ctx) return;

    const topData = dataArray.slice(0, 6); 
    const labels = topData.map(d => d.type);
    const values = topData.map(d => d.total);

    if (pieChart) pieChart.destroy();

    pieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: ['#164ab8', '#f57e20', '#27ae60', '#e74c3c', '#8e44ad', '#34495e'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: { 
                    position: 'bottom', 
                    labels: { 
                        boxWidth: 12, 
                        // Fuente aumentada como pediste
                        font: { size: 14, weight: 'bold' },
                        padding: 20 
                    } 
                }
            }
        }
    });
}

function updateTypeTable(dataArray) {
    const tbody = document.getElementById('typeTable');
    if (!tbody) return;
    tbody.innerHTML = '';

    dataArray.forEach(item => {
        const row = document.createElement('tr');
        row.className = 'border-b border-gray-100 hover:bg-gray-50 transition';
        
        // Colorear badge según confianza del modelo
        const confVal = parseInt(item.confidence);
        const badgeColor = confVal > 90 ? 'text-green-700 bg-green-100' : 'text-blue-700 bg-blue-100';

        row.innerHTML = `
            <td class="py-3 px-6 text-gray-700 font-medium">${item.type}</td>
            <td class="text-center py-3 px-6 text-gray-600">${item.total}</td>
            
            <!-- Intervalo Estándar (Lo que dice la norma) -->
            <td class="text-center py-3 px-6 text-gray-500">${item.stdInterval} d</td>
            
            <!-- Intervalo Optimizado (Lo que dice tu modelo XGBoost) -->
            <td class="text-center py-3 px-6 font-bold text-green-600">${item.optInterval} d</td>
            
            <!-- Confianza (El R2 de tu entrenamiento) -->
            <td class="text-center py-3 px-6">
                <span class="${badgeColor} px-2 py-1 rounded text-xs font-bold">${item.confidence}</span>
            </td>
        `;
        tbody.appendChild(row);
    });
}