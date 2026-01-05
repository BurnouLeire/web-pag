let histogramChart, pieChart;

// --- Mock Data (Datos de Prueba) ---
// Esta es la estructura que tu API (Supabase) debería idealmente devolver.
const mockData = {
    expired: 5,
    upcoming: 12,
    calibratedThisMonth: 24,
    calibrationByMonth: {
        labels: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio'],
        data: [8, 12, 15, 10, 20, 24]
    },
    // Modificamos esto: ahora es un array de objetos, 
    // con toda la información necesaria para la tabla.
    instrumentTypes: [
        { type: 'Manómetros', total: 45, expired: 2, upcoming: 5, vigent: 38 },
        { type: 'Vacuómetros', total: 28, expired: 0, upcoming: 3, vigent: 25 },
        { type: 'Indicadores de Presión', total: 52, expired: 3, upcoming: 10, vigent: 39 },
        { type: 'Manovacuómetros', total: 35, expired: 0, upcoming: 1, vigent: 34 }
    ]
};

// --- Inicialización del Dashboard ---

// 1. Espera a que el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Llama a la función asíncrona principal
    initDashboardAsync();
});

// 2. Función asíncrona principal que obtiene datos y luego dibuja la UI
async function initDashboardAsync() {
    try {
        // Muestra un 'cargando...' mientras se obtienen los datos (opcional)
        // updateUILoading(true); 

        // Obtiene los datos (actualmente de mockData, 
        // pero esperará si fetchDashboardData usa Supabase)
        const data = await fetchDashboardData();

        // 3. Una vez tenemos datos, actualizamos todos los componentes
        
        // Actualizar tarjetas de métricas
        document.getElementById('expired-count').textContent = data.expired;
        document.getElementById('upcoming-count').textContent = data.upcoming;
        document.getElementById('calibrated-count').textContent = data.calibratedThisMonth;

        // Inicializar gráficos y tabla pasando los datos
        initHistogram(data.calibrationByMonth);
        initPieChart(data.instrumentTypes);
        updateTypeTable(data.instrumentTypes);

        // Oculta el 'cargando...' (opcional)
        // updateUILoading(false);

    } catch (error) {
        console.error("Error al inicializar el dashboard:", error);
        // Aquí podrías mostrar un mensaje de error en la UI
    }
}


// --- Funciones de Gráficos y Tabla (Ahora reciben datos) ---

function initHistogram(calibrationData) {
    const ctx = document.getElementById('histogramChart').getContext('2d');
    
    // Destruye el gráfico anterior si existe (para evitar errores al recargar)
    if (histogramChart) {
        histogramChart.destroy();
    }

    histogramChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: calibrationData.labels,
            datasets: [{
                label: 'Instrumentos Calibrados',
                data: calibrationData.data,
                backgroundColor: [
                    '#164ab8', '#1a5fd4', '#f57e20', 
                    '#ff9a3d', '#27ae60', '#52be80'
                ],
                borderColor: '#ffffff',
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#b0c4de', font: { size: 12 } }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#b0c4de' },
                    grid: { color: 'rgba(22, 74, 184, 0.1)' }
                },
                x: {
                    ticks: { color: '#b0c4de' },
                    grid: { display: false }
                }
            }
        }
    });
}

function initPieChart(instrumentData) {
    const ctx = document.getElementById('pieChart').getContext('2d');
    
    // Extrae etiquetas y valores del array de objetos
    const labels = instrumentData.map(item => item.type);
    const values = instrumentData.map(item => item.total);
    
    // Destruye el gráfico anterior si existe
    if (pieChart) {
        pieChart.destroy();
    }

    pieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: ['#164ab8', '#f57e20', '#27ae60', '#e74c3c'],
                borderColor: '#1a3a5c',
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#b0c4de', font: { size: 12 }, padding: 20 }
                }
            }
        }
    });
}

function updateTypeTable(typeDataArray) {
    const tableBody = document.getElementById('typeTable');
    tableBody.innerHTML = ''; // Limpia el contenido anterior

    // Itera sobre el array de datos y crea una fila por cada item
    typeDataArray.forEach(item => {
        const row = document.createElement('tr');
        row.className = 'border-b border-[#164ab8]/20 hover:bg-[#164ab8]/10 transition';
        
        // Ya no usamos Math.random(), usamos los datos reales del objeto
        row.innerHTML = `
            <td class="py-3 px-4 text-white font-medium">${item.type}</td>
            <td class="text-center py-3 px-4 text-white font-bold">${item.total}</td>
            <td class="text-center py-3 px-4 text-[#ff6b6b] font-semibold">${item.expired}</td>
            <td class="text-center py-3 px-4 text-[#ffc107] font-semibold">${item.upcoming}</td>
            <td class="text-center py-3 px-4 text-[#52be80] font-semibold">${item.vigent}</td>
        `;
        tableBody.appendChild(row);
    });
}

// --- Función de Obtención de Datos (Lista para Supabase) ---

async function fetchDashboardData() {
    try {
        // -----------------------------------------------------------------
        // INICIO: Bloque para descomentar cuando conectes Supabase
        // -----------------------------------------------------------------

        /*
        // NOTA: 'window.supabaseClient' debe estar definido globalmente
        // (usualmente en auth.js o un archivo principal)

        // 1. Obtener todos los instrumentos
        const { data: instruments, error } = await window.supabaseClient
             .from('instruments') // Asegúrate que tu tabla se llame 'instruments'
             .select('calibration_date, next_calibration, instrument_type');
        
        if (error) throw error;

        // 2. Procesar los datos (esto es un ejemplo, 
        //    idealmente esto lo haría una 'Edge Function' en Supabase)
        
        const now = new Date();
        const thirtyDaysFromNow = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
        const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);

        let expired = 0;
        let upcoming = 0;
        let calibratedThisMonth = 0;
        const typeMap = {};
        const monthMap = {}; // Para el histograma

        instruments.forEach(inst => {
            const nextCal = new Date(inst.next_calibration);
            const lastCal = new Date(inst.calibration_date);
            const type = inst.instrument_type || 'Sin Tipo';

            // Inicializa el contador para este tipo
            if (!typeMap[type]) {
                typeMap[type] = { type: type, total: 0, expired: 0, upcoming: 0, vigent: 0 };
            }
            typeMap[type].total++;

            // Contar estados
            if (nextCal < now) {
                expired++;
                typeMap[type].expired++;
            } else if (nextCal >= now && nextCal <= thirtyDaysFromNow) {
                upcoming++;
                typeMap[type].upcoming++;
            } else {
                typeMap[type].vigent++;
            }

            // Contar calibrados este mes
            if (lastCal >= startOfMonth) {
                calibratedThisMonth++;
            }
            
            // Contar para el histograma (ej. últimos 6 meses)
            // (Esta lógica requiere más detalle, pero es la idea)
            const monthLabel = lastCal.toLocaleString('es-ES', { month: 'long' });
            // ... (lógica para agrupar por mes)
        });

        // 3. Formatear datos para el dashboard
        const processedData = {
            expired: expired,
            upcoming: upcoming,
            calibratedThisMonth: calibratedThisMonth,
            calibrationByMonth: { // Deberías construir esto con la lógica de monthMap
                labels: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio'],
                data: [8, 12, 15, 10, 20, 24] // Dato de ejemplo
            },
            instrumentTypes: Object.values(typeMap)
        };
        
        return processedData;
        
        */

        // -----------------------------------------------------------------
        // FIN: Bloque Supabase
        // -----------------------------------------------------------------

        // Por ahora, devolvemos los datos de prueba después de 0.5 seg
        // para simular una carga de red.
        await new Promise(resolve => setTimeout(resolve, 500));
        console.log("Usando mockData (simulación de carga)");
        return mockData;

    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        // En caso de error, devuelve mockData para que la app no se rompa
        return mockData;
    }
}