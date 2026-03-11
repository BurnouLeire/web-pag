// ============================================
// ESPERAR A QUE LA PÁGINA CARGUE
// ============================================
document.addEventListener("DOMContentLoaded", () => {
  let calibrationChart = null;

  // ============================================
  // FUNCIÓN DE BÚSQUEDA PRINCIPAL
  // ============================================
  window.buscarInstrumento = async () => {
    const codigo = document.getElementById("codigoInstrumento").value.trim();

    if (!codigo) {
      mostrarError("Por favor ingresa un código de instrumento");
      return;
    }

    ocultarTodo();
    document.getElementById("loading").classList.add("show");
    document.getElementById("btnBuscar").disabled = true;

    try {
      console.log("🔍 Buscando instrumento:", codigo);

      const response = await fetch("/laboratorio/buscar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codigo }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Error al buscar instrumento");
      }

      const data = await response.json();
      console.log("✓ Datos recibidos del servidor:", data);

      // Mostrar información del instrumento
      mostrarInfoInstrumento(data.instrumento);

      // Mostrar resultado de la predicción
      mostrarResultado(data.prediccion, data.instrumento);

      // Mostrar gráfico con el historial
      mostrarGraficoTendencia(
        data.historial,
        data.predicciones_historicas,
        data.prediccion.dias_hasta_siguiente,
        data.prediccion.fecha_estimada
      );
    } catch (error) {
      console.error("❌ Error:", error);
      mostrarError(error.message);
    } finally {
      document.getElementById("loading").classList.remove("show");
      document.getElementById("btnBuscar").disabled = false;
    }
  };

  // ============================================
  // MOSTRAR INFORMACIÓN DEL INSTRUMENTO
  // ============================================
  function mostrarInfoInstrumento(instrumento) {
    document.getElementById("infoCodigo").textContent = instrumento.codigo;

    const infoFields = [
      { label: "Tipo", value: instrumento.tipo || "N/A" },
      { label: "Marca", value: instrumento.marca || "N/A" },
      { label: "Instrumento", value: instrumento.instrumento || "N/A" },
      { label: "Unidad", value: instrumento.unidad || "N/A" },
      {
        label: "Última Calibración",
        value: formatearFecha(instrumento.fecha_calibracion),
      },
      {
        label: "Temperatura",
        value: instrumento.temperatura ? `${instrumento.temperatura}°C` : "N/A",
      },
      {
        label: "Humedad",
        value: instrumento.humedad ? `${instrumento.humedad}%` : "N/A",
      },
    ];

    const grid = document.getElementById("infoGrid");
    grid.innerHTML = infoFields
      .map(
        (field) => `
      <div class="info-item">
        <div class="info-label">${field.label}</div>
        <div class="info-value">${field.value}</div>
      </div>
    `
      )
      .join("");

    document.getElementById("instrumentInfo").classList.add("show");
  }

  // ============================================
  // MOSTRAR RESULTADO DE PREDICCIÓN
  // ============================================
  function mostrarResultado(prediccion, instrumento) {
    document.getElementById("diasResultado").textContent =
      `${prediccion.dias_hasta_siguiente} días`;
    document.getElementById("mesesResultado").textContent =
      prediccion.meses_aproximados;
    document.getElementById("semanasResultado").textContent =
      prediccion.semanas_aproximadas;
    document.getElementById("fechaEstimada").textContent =
      `Fecha estimada: ${formatearFecha(prediccion.fecha_estimada)}`;

    document.getElementById("resultCard").classList.add("show");

    setTimeout(() => {
      document.getElementById("resultCard").scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }, 100);
  }



  // ============================================
  // MOSTRAR GRÁFICO DE TENDENCIA - VERSIÓN SIMPLIFICADA
  // ============================================
  function mostrarGraficoTendencia(historial, prediccionesHistoricas, diasPredichos, fechaEstimada) {
    try {
      // 1. PREPARAR FECHAS (Formato completo DD/MM/YYYY)
      // Usamos todas las fechas del historial + la fecha futura predicha
      const todasLasFechas = historial.map(h => formatearFechaDDMM(h.fecha_calibracion));
      const fechaFuturaObj = new Date(fechaEstimada);
      todasLasFechas.push(formatearFechaDDMM(fechaFuturaObj));
      // Índices para el sombreado
      const indiceUltimoReal = historial.length - 1;
      const indicePrediccion = todasLasFechas.length - 1;

      // 2. CALCULAR DÍAS REALES (Línea Azul)
      // Igual que en tu guía de Python: empezamos en 0
      let diasReales = [0];
      for (let i = 1; i < historial.length; i++) {
        const actual = new Date(historial[i].fecha_calibracion);
        const anterior = new Date(historial[i - 1].fecha_calibracion);
        const diff = Math.round((actual - anterior) / (1000 * 60 * 60 * 24));
        diasReales.push(diff);
      }
      diasReales.push(null); // Espacio para el punto futuro

      // 3. PREPARAR PREDICCIONES ML (Línea Verde)
      // Mantenemos los valores que vienen del servidor y agregamos null al final
      let diasML = [...prediccionesHistoricas, null];

      // 4. PUNTO ROJO (Predicción Futura)
      let puntoRojo = new Array(todasLasFechas.length).fill(null);
      puntoRojo[puntoRojo.length - 1] = diasPredichos;

      // 5. CONFIGURACIÓN DEL GRÁFICO
      const ctx = document.getElementById("calibrationChart").getContext("2d");
      if (calibrationChart) calibrationChart.destroy();

      calibrationChart = new Chart(ctx, {
        type: "line",
        data: {
          labels: todasLasFechas,
          datasets: [
            {
              label: "Calibraciones Reales",
              data: diasReales,
              // Azul brillante y limpio
              borderColor: "#3b82f6",
              backgroundColor: "rgba(59, 130, 246, 0.1)", // Fondo suave azul
              borderWidth: 4,
              pointRadius: 6,
              pointBackgroundColor: "#3b82f6",
              pointBorderColor: "#fff",
              pointBorderWidth: 2,
              //fill: true, // Relleno suave para dar volumen
              tension: 0.3
            },
            {
              label: "Prediccion",
              data: diasML,
              // Verde esmeralda brillante
              borderColor: "#10b981",
              backgroundColor: "transparent",
              borderWidth: 3,
              borderDash: [6, 6], // Línea punteada clara
              pointRadius: 7,
              pointStyle: 'rectRot', // Diamante para variar
              pointBackgroundColor: "#10b981",
              pointBorderColor: "#fff",
              pointBorderWidth: 2,
              fill: false,
              tension: 0.3
            },
            {
              label: "Próxima Calibración",
              data: puntoRojo,
              // Rojo vibrante
              borderColor: "#ef4444",
              backgroundColor: "#ef4444",
              pointRadius: 10,
              pointHoverRadius: 15,
              pointStyle: 'circle',
              pointBorderColor: "#fff",
              pointBorderWidth: 4,
              showLine: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          // Fondo del área del gráfico (blanco puro)
          plugins: {
            legend: {
              labels: {
                color: "#3565a8ff", // Gris muy oscuro casi negro para leer bien
                font: { size: 13, weight: 'bold' }
              }
            },
            tooltip: {
              backgroundColor: "rgba(255, 255, 255, 0.9)", // Tooltip blanco
              titleColor: "#111827",
              bodyColor: "#111827",
              borderColor: "#e5e7eb",
              borderWidth: 1,
              padding: 12,
              displayColors: true,
              bodyFont: { size: 14 }
            },
            annotation: {
              annotations: {
                zonaRoja: {
                  type: 'box',
                  xMin: indiceUltimoReal,
                  xMax: indicePrediccion,
                  backgroundColor: 'rgba(239, 68, 68, 0.1)', // Rojo muy suave (Red 500)
                  borderWidth: 0,
                  z: -1 // Para que quede detrás de las líneas
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false // Quitamos las líneas verticales para que se vea más limpio
              },
              ticks: {
                color: "#4b5563", // Gris medio para las fechas
                font: { size: 11, weight: '500' },
                maxRotation: 45,
                minRotation: 45,
                autoSkip: false
              }
            },
            y: {
              beginAtZero: true,
              grid: {
                color: "#f3f4f6", // Líneas horizontales muy claritas (casi invisibles)
                drawBorder: false
              },
              ticks: {
                color: "#346ab4ff",
                font: { size: 12 },
                callback: (val) => val + " d" // Abreviatura de días
              }
            }
          }
        }
      });
      document.getElementById("trendChart").classList.add("show");
    } catch (e) {
      console.error("Error en gráfico:", e);
    }
  }

  // NUEVA FUNCIÓN AUXILIAR PARA FECHA CORREGIDA
  function formatearFechaDDMM(fechaStr) {
    const fecha = new Date(fechaStr);
    if (isNaN(fecha)) return "S/F";
    // Forzamos el formato día/mes/año
    const dia = String(fecha.getDate()).padStart(2, '0');
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const anio = fecha.getFullYear();
    return `${dia}/${mes}/${anio}`;
  }

  // ============================================
  // FUNCIONES AUXILIARES
  // ============================================
  function mostrarError(mensaje) {
    const errorDiv = document.getElementById("errorMessage");
    errorDiv.textContent = "❌ " + mensaje;
    errorDiv.classList.add("show");

    if (!mensaje.includes("crítico")) {
      setTimeout(() => {
        errorDiv.classList.remove("show");
      }, 5000);
    }
  }

  function ocultarTodo() {
    document.getElementById("errorMessage").classList.remove("show");
    document.getElementById("instrumentInfo").classList.remove("show");
    document.getElementById("resultCard").classList.remove("show");
    document.getElementById("trendChart").classList.remove("show");
  }

  function formatearFecha(fechaStr) {
    if (!fechaStr) return "N/A";

    const fecha = new Date(fechaStr);

    if (isNaN(fecha.getTime())) {
      console.warn("⚠️ Fecha inválida:", fechaStr);
      return "Fecha inválida";
    }

    return fecha.toLocaleDateString("es-ES", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  function formatearFechaCorta(fecha) {
    if (!fecha) return "N/A";

    let date = fecha instanceof Date ? fecha : new Date(fecha);

    if (isNaN(date.getTime())) {
      return "Fecha inválida";
    }

    return date.toLocaleDateString("es-ES", {
      year: "2-digit",
      month: "short",
    });
  }

  // ============================================
  // EVENT LISTENERS
  // ============================================
  document
    .getElementById("codigoInstrumento")
    ?.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        window.buscarInstrumento();
      }
    });
});