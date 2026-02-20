# 🔬 Sistema de Predicción de Intervalos de Calibración (ML)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![Supabase](https://img.shields.io/badge/Supabase-Database-emerald)
![Machine Learning](https://img.shields.io/badge/AI-Scikit--Learn-orange)
![Node](https://img.shields.io/badge/Node.js-18%2B-brightgreen)

> **Optimización de mantenimiento industrial mediante Inteligencia Artificial.**

Este proyecto es una aplicación web que utiliza algoritmos de **Machine Learning (Regresión)** para predecir la fecha óptima de calibración de instrumentos (manómetros, vacuómetros, etc.).


---

# 🚀 Características Principales

- 🧠 **Motor de IA:** Modelo predictivo entrenado con Scikit-Learn.
- 📊 **Dashboard Estratégico:** Visualización de métricas y carga de trabajo.
- 🧪 **Módulo de Laboratorio:** Ingreso de certificados con predicción en tiempo real.
- ☁️ **Integración Cloud:** Conexión con Supabase.
- 🏗️ **Arquitectura 3 Capas:** Presentación, Lógica y Datos.

---

# 🛠️ Arquitectura del Proyecto

## 🔹 Capas del Sistema

1. **Presentación:** Rutas Flask (`routes/`), Vistas (`templates/`, `static/`)
2. **Lógica de Negocio:** Servicios (`services/`)
3. **Datos:** Supabase + persistencia del modelo (`models/`)

---

## 📂 Estructura del Proyecto

```text
PROYECTO/
├── app/
│   ├── models/                # Modelo .pkl y cargadores
│   ├── routes/                # Controladores (Dashboard, API, Lab)
│   ├── services/              # Lógica (Feature Engineering, Prediction)
│   ├── static/                # JS, CSS
│   └── templates/             # HTML (Jinja2)
├── node_modules/              # Dependencias de frontend (NO subir a Git)
├── .env.example
├── requirements.txt
├── package.json
└── run.py
```

---

# 💻 Requisitos Previos

Instalar en tu máquina:

- Python 3.9+
- Node.js 18+ (solo si usas Tailwind, Chart.js vía npm o build tools)
- Git

---

# ⚙️ Instalación Completa

## 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/NOMBRE_DEL_REPO.git
cd NOMBRE_DEL_REPO
```

---

## 2️⃣ Crear entorno virtual (Backend)

```bash
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
```

---

## 3️⃣ Instalar dependencias Python

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Instalar dependencias Frontend (Node)

⚠️ Solo si el proyecto usa Tailwind, PostCSS, Vite u otros paquetes npm.

```bash
npm install
```

Esto generará automáticamente la carpeta:

```
node_modules/
```
# 🔐 Configuración de Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```
# Configuración Flask
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY="genera_una_clave_segura_aqui"

# Configuración Supabase
SUPABASE_URL="https://tu-proyecto.supabase.co"
SUPABASE_KEY="tu-clave-anon-publica_aqui"
```

---

# ▶️ Ejecutar la Aplicación

## Backend

```bash
python run.py
```


---

# 📊 Tecnologías Utilizadas

- Python
- Flask
- Scikit-Learn
- Supabase
- TailwindCSS
- Chart.js
- Node.js

---

# 📈 Flujo del Sistema

1. Usuario ingresa datos históricos de calibración.
2. Se realiza Feature Engineering.
3. El modelo predice deriva futura.
4. Se calcula intervalo óptimo.
5. Se visualiza recomendación en dashboard.

---

# 🧠 Modelo de Machine Learning

- Tipo: Regresión Supervisada
- Librería: Scikit-Learn
- Persistencia: Archivo `.pkl`
- Entrada: Deriva histórica + condiciones ambientales
- Salida: Fecha o intervalo óptimo de recalibración

---

# 🚀 Despliegue

Puede desplegarse en:

- Render
---

# 📌 Notas Importantes

- El modelo `.pkl` debe estar dentro de `app/models/`
- No subir `.env`
- No subir `venv`
- No subir `node_modules`

---

# 👨‍🔬 Autor

AVO / RCE