# 🔬 Sistema de Predicción de Intervalos de Calibración (ML)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![Supabase](https://img.shields.io/badge/Supabase-Database-emerald)
![Machine Learning](https://img.shields.io/badge/AI-Scikit--Learn-orange)

> **Optimización de mantenimiento industrial mediante Inteligencia Artificial.**

Este proyecto es una aplicación web full-stack que utiliza algoritmos de **Machine Learning (Regresión)** para predecir la fecha óptima de calibración de instrumentos de medición (manómetros, vacuómetros, etc.). El sistema analiza el historial de deriva instrumental y condiciones ambientales para sugerir intervalos dinámicos, reemplazando el enfoque tradicional de "calendario fijo".

---

## 🚀 Características Principales

*   **🧠 Motor de IA:** Modelo predictivo entrenado con Scikit-Learn que calcula la degradación del instrumento.
*   **📊 Dashboard Estratégico:** Visualización de métricas clave, histogramas de carga de trabajo y comparación de ahorro (Días ganados vs Riesgo).
*   **🧪 Módulo de Laboratorio:** Interfaz para ingresar nuevos certificados y obtener predicciones en tiempo real.
*   **☁️ Arquitectura Cloud:** Integración nativa con **Supabase** para gestión de datos históricos y autenticación.
*   **🏗️ Arquitectura Modular:** Diseño basado en **3 Capas (Presentación, Lógica, Datos)** para escalabilidad.

---

## 🛠️ Arquitectura del Proyecto

El sistema sigue una arquitectura limpia separando responsabilidades:

1.  **Capa de Presentación:** Rutas Flask (`routes/`) y Vistas (`templates/` + `static/`).
2.  **Capa de Lógica de Negocio:** Servicios (`services/`) que manejan la ingeniería de características y la inferencia del modelo.
3.  **Capa de Datos:** Conexión con Supabase y persistencia del modelo (`models/`).

### Estructura de Carpetas

```text
PROYECTO/
├── app/
│   ├── models/                # Modelo .pkl y cargadores
│   ├── routes/                # Controladores (Dashboard, API, Lab)
│   ├── services/              # Lógica (Feature Engineering, Prediction)
│   ├── static/                # JS (Chart.js), CSS (Tailwind)
│   └── templates/             # HTML (Jinja2)
├── .env.example               # Ejemplo de configuración
├── requirements.txt           # Dependencias
└── run.py                     # Punto de entrada


## 💻 Instalación y Configuración

git clone https://github.com/TU_USUARIO/NOMBRE_DEL_REPO.git
cd NOMBRE_DEL_REPO

Crear el Entorno Virtual
python -m venv venv
.\venv\Scripts\activate

 Instalar Dependencias
 pip install -r requirements.txt

 Configuración de Variables de Entorno

 # Archivo: .env

# Configuración de Flask
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY="genera_una_clave_segura_aqui"

# Configuración de Supabase (Base de Datos & Auth)
SUPABASE_URL="https://tu-proyecto.supabase.co"
SUPABASE_KEY="tu-clave-anon-publica-aqui"