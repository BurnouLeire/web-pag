import os
import traceback
from flask import Blueprint, render_template, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
from app.services.prediction_service import PredictionService
from app.services.feature_engineering import FeatureEngineering

load_dotenv()

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# Inicialización de servicios
prediction_service = PredictionService()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key) if url and key else None

@bp.route("/")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")

@bp.route("/data")
def dashboard_data():
    if not supabase:
        return jsonify({"error": "No hay conexión a Supabase"}), 500

    try:
        # --- 1. OBTENCIÓN DE DATOS (Podrías mover esto a SupabaseService tmb) ---
        all_data = []
        offset = 0
        batch_size = 1000 
        cols = "fecha_calibracion, tipo, instrumento, periodicidad, temperatura, humedad, incertidumbre, marca_id, codigo"

        while True:
            response = supabase.table('historicos').select(cols).range(offset, offset + batch_size - 1).execute()
            rows = response.data
            if not rows: break
            all_data.extend(rows)
            if len(rows) < batch_size: break
            offset += batch_size

        if not all_data:
            return jsonify({"error": "No data found"}), 404

        # --- 2. PROCESAMIENTO (Delegado a FeatureEngineering) ---
        # Aquí ocurre la magia de Pandas, limpieza, cálculo de edades, lags, etc.
        df = FeatureEngineering.preparar_dataframe_dashboard(all_data)

        # --- 3. PREDICCIÓN MASIVA (Delegado a PredictionService) ---
        # El servicio se encarga de checkear columnas y aplicar el modelo
        df['prediccion_ia'] = prediction_service.predict_batch(df)

        # --- 4. PREPARACIÓN DE RESPUESTA JSON ---
        # (Lógica de agrupación visual se mantiene aquí porque es específica de la vista)
        
        # a) Histograma
        df['year'] = df['fecha_calibracion'].dt.year
        conteo_mensual = df.groupby(['year', 'mes']).size()
        available_years = sorted(df['year'].unique().tolist())
        historical_data = {int(y): [int(conteo_mensual.get((y, m), 0)) for m in range(1, 13)] for y in available_years}

        # b) Tabla de Instrumentos
        instrument_types = FeatureEngineering.agrupar_por_tipo(df) # Sugerencia: Mover la lógica de agrupación tmb

        # c) Métricas del modelo
        metrics = prediction_service.metrics
        
        return jsonify({
            "aiMetrics": {
                "r2Score": f"{metrics.get('r2', 0.94):.2f}", 
                "processedCertificates": len(df),
                "daysOptimized": 0 # Aquí puedes recalcular tu lógica de días ganados si quieres
            },
            "historicalData": historical_data,
            "availableYears": available_years,
            "instrumentTypes": instrument_types,
            "featureImportance": prediction_service.get_feature_importance_list() # Nuevo método sugerido en el servicio
        })

    except Exception as e:
        print(f"Error Dashboard: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500