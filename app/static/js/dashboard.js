/**
 * DASHBOARD ESTRATÉGICO FINAL - RIVALESA ML
 */
let histogramChart, pieChart, importanceChart;
let allHistoricalData = {};
const CACHE_KEY = 'dashboard_v5_final_fix';

const mockData = {
    aiMetrics: { r2Score: 0.94, processedCertificates: 4419 }, 
    historicalData: { 2025: [190, 150, 70, 100, 20, 130, 60, 30, 0, 0, 0, 0], 2024: [180, 140, 90, 110, 40, 120, 70, 40, 100, 110, 130, 150] },
    availableYears: [2024, 2025],
    featureImportance: [
        { variable: "Deriva Histórica", importance: 45 },
        { variable: "Ciclos de Uso", importance: 25 },
        { variable: "Error Máximo", importance: 15 },
        { variable: "Antigüedad", importance: 10 },
        { variable: "Condición Ambiental", importance: 5 }
    ],
    instrumentTypes: [
        { type: "Manómetro", total: 1850, stdInterval: 365, optInterval: 415 },
        { type: "Manovacuómetro", total: 450, stdInterval: 365, optInterval: 210 },
        { type: "Indicador Presión Digital", total: 320, stdInterval: 365, optInterval: 425 },
        { type: "Vacuómetro", total: 120, stdInterval: 365, optInterval: 365 }
    ]
};

document.addEventListener('DOMContentLoaded', () => initDashboardAsync());

async function initDashboardAsync() {
    try {
        const data = await fetchDashboardData();
        if (!data) return;

        // 1. KPIs
        document.getElementById('r2-score').textContent = data.aiMetrics?.r2Score || "0.94";
        document.getElementById('total-certs').textContent = (data.aiMetrics?.processedCertificates || 0).toLocaleString();

        // 2. Variables Críticas (DATOS REALES DESDE PYTHON)
        if (data.featureImportance && Array.isArray(data.featureImportance)) {
            initImportanceChart(data.featureImportance);
        }

        // 3. Otros componentes...
        if (data.instrumentTypes) {
            initPieChart(data.instrumentTypes);
            updateTypeTable(data.instrumentTypes);
        }
        
        if (data.historicalData) {
            allHistoricalData = data.historicalData;
            setupYearSelector(data.availableYears);
            initHistogram(Math.max(...data.availableYears));
        }

    } catch (e) {
        console.error("Error al cargar datos reales:", e);
    }
}

async function fetchDashboardData() {
    try {
        const response = await fetch('/dashboard/data');
        return response.ok ? await response.json() : mockData;
    } catch { return mockData; }
}

// --- GRÁFICOS ---

function initImportanceChart(features) {
    const ctx = document.getElementById('importanceChart')?.getContext('2d');
    if (!ctx || !features) return;
    if (importanceChart) importanceChart.destroy();

    const sortedFeatures = [...features].sort((a, b) => b.importance - a.importance);
    const gradient = ctx.createLinearGradient(0, 0, 600, 0);
    gradient.addColorStop(0, '#fbbf24'); gradient.addColorStop(1, '#f59e0b');

    importanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedFeatures.map(f => f.variable),
            datasets: [{
                label: 'Peso (%)',
                data: sortedFeatures.map(f => f.importance),
                backgroundColor: gradient, borderRadius: 6, barThickness: 25
            }]
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' } } }
        }
    });
}

function initPieChart(dataArray) {
    const ctx = document.getElementById('pieChart')?.getContext('2d');
    if (!ctx) return;
    if (pieChart) pieChart.destroy();
    pieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: dataArray.map(d => d.type),
            datasets: [{
                data: dataArray.map(d => d.total),
                backgroundColor: ['#1e40af', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '70%',
            plugins: { legend: { position: 'right', labels: { usePointStyle: true } } }
        }
    });
}

function updateTypeTable(dataArray) {
    const tbody = document.getElementById('typeTable');
    if (!tbody) return;
    tbody.innerHTML = '';
    dataArray.forEach(item => {
        const ajuste = item.optInterval - item.stdInterval;
        const badge = ajuste > 0 ? "bg-green-100 text-green-700 border-green-200" : (ajuste < 0 ? "bg-red-100 text-red-700 border-red-200" : "bg-gray-100 text-gray-600");
        const texto = ajuste > 0 ? `+${ajuste} días (Ahorro)` : (ajuste < 0 ? `${ajuste} días (Riesgo)` : "Óptimo");

        tbody.innerHTML += `
            <tr class="hover:bg-gray-50 transition">
                <td class="py-4 px-6 font-medium">${item.type}</td>
                <td class="text-center py-4 px-6 text-gray-400 font-mono">${item.stdInterval} d</td>
                <td class="text-center py-4 px-6 font-bold text-blue-700 bg-blue-50/50">${item.optInterval} d</td>
                <td class="text-center py-4 px-6">
                    <span class="px-3 py-1 rounded-full text-xs font-bold border ${badge}">${texto}</span>
                </td>
            </tr>`;
    });
}

function setupYearSelector(years) {
    const selector = document.getElementById('yearFilter');
    if(!selector) return;
    selector.innerHTML = years.sort((a,b)=>b-a).map(y => `<option value="${y}">Año ${y}</option>`).join('');
    selector.addEventListener('change', (e) => {
        histogramChart.data.datasets[0].data = allHistoricalData[e.target.value];
        histogramChart.update();
    });
}

function initHistogram(year) {
    const ctx = document.getElementById('histogramChart')?.getContext('2d');
    if (!ctx) return;
    histogramChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'],
            datasets: [{ label: 'Equipos', data: allHistoricalData[year], backgroundColor: '#164ab8', borderRadius: 4 }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
    });
}