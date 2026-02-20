from flask import Blueprint, render_template, request, jsonify
import os
from datetime import timedelta
from dotenv import load_dotenv
from app.services.supabase_service import SupabaseService
from app.services.prediction_service import PredictionService
from app.services.feature_engineering import FeatureEngineering

load_dotenv()

bp = Blueprint("laboratorio", __name__, url_prefix="/laboratorio")

# Inicializar servicios
prediction_service = PredictionService()
supabase_service = SupabaseService()

@bp.route("/")
def index():
    return render_template(
        "laboratorio.html", 
        active_page="laboratorio",
        supabase_url=os.getenv('SUPABASE_URL', ''),
        supabase_key=os.getenv('SUPABASE_KEY', '')
    )

@bp.route("/buscar", methods=["POST"])
def buscar_instrumento():
    try:
        data = request.json
        codigo = data.get('codigo', '').strip().upper()
        
        # 1. Obtener datos de Supabase
        instrumento = supabase_service.buscar_instrumento(codigo)
        if not instrumento: return jsonify({'error': 'No encontrado'}), 404
        
        historial = supabase_service.obtener_historial_completo(codigo)
        # Ordenar historial cronológicamente
        historial = sorted(historial, key=lambda x: x['fecha_calibracion'])
        
        # 2. Predicción Futura (Estado Actual)
        features_raw = supabase_service.extraer_features(instrumento, codigo)
        
        # Calcular edad actual usando la lógica centralizada
        fecha_primera = FeatureEngineering.parsear_fecha(historial[0]['fecha_calibracion'])
        fecha_ultima = FeatureEngineering.parsear_fecha(historial[-1]['fecha_calibracion'])
        
        features_raw['edad_operacional'] = FeatureEngineering.calcular_edad_meses(fecha_ultima, fecha_primera)
        
        # Predecir usando el servicio
        dias_futuros, meses_futuros = prediction_service.predict_single(features_raw)
        fecha_estimada = fecha_ultima + timedelta(days=dias_futuros)

        # 3. Reconstrucción Histórica
        predicciones_historicas = [0] # El primer punto no tiene predicción previa
        features_limpias_debug = prediction_service.limpiar_features(features_raw) # Para devolver al front

        # Datos estáticos para el bucle
        datos_estaticos = {
            'marca_id': features_raw.get('marca_id', 0),
            'incertidumbre': features_raw.get('incertidumbre', 0),
            'temperatura': features_raw.get('temperatura', 20),
            'humedad': features_raw.get('humedad', 50)
        }

        for i in range(1, len(historial)):
            try:
                # Usamos el servicio estático para calcular las variables del pasado
                f_hist, _ = FeatureEngineering.calcular_features_historicas(
                    item_actual=historial[i],
                    item_previo=historial[i-1],
                    datos_estaticos=datos_estaticos,
                    fecha_primera_dt=fecha_primera
                )
                
                # Predecir
                val_pred, _ = prediction_service.predict_single(f_hist)
                predicciones_historicas.append(val_pred)

            except Exception as e:
                print(f"Error en historial {i}: {e}")
                predicciones_historicas.append(0)

        # 4. Respuesta
        return jsonify({
            'instrumento': instrumento,
            'prediccion': {
                'dias_hasta_siguiente': dias_futuros,
                'meses_aproximados': meses_futuros,
                'fecha_estimada': fecha_estimada.isoformat()
            },
            'historial': historial,
            'predicciones_historicas': predicciones_historicas,
            'features': features_limpias_debug
        })

    except Exception as e:
        print(f"❌ Error Laboratorio: {e}")
        return jsonify({'error': str(e)}), 500

# Endpoint API redundante (ya existe api.py, pero si lo usas interno lo dejamos limpio)
@bp.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json
        dias, meses = prediction_service.predict_single(data)
        return jsonify({"dias_hasta_siguiente": dias, "meses_aproximados": meses})
    except Exception as e:
        return jsonify({'error': str(e)}), 500