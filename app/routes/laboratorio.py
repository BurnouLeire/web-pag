from flask import Blueprint, render_template, request, jsonify
import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from app.models.model_loader import cargar_modelo
from app.services.supabase_service import SupabaseService

bp = Blueprint("laboratorio", __name__, url_prefix="/laboratorio")

# Cargar modelo al inicio
modelo, feature_cols = cargar_modelo()

# Inicializar servicio de Supabase
try:
    supabase_service = SupabaseService()
except ValueError as e:
    print(f"⚠️ ADVERTENCIA: {e}")
    supabase_service = None

@bp.route("/")
def index():
    return render_template(
        "laboratorio.html", 
        active_page="laboratorio",
        supabase_url=os.getenv('SUPABASE_URL', ''),
        supabase_key=os.getenv('SUPABASE_KEY', '')
    )

def limpiar_features(features_dict, feature_cols):
    """
    Limpia features asegurando float y quitando infinitos.
    """
    features_limpias = {}
    for col in feature_cols:
        valor = features_dict.get(col, 0)
        try:
            valor_float = float(valor) if valor is not None else 0.0
        except (ValueError, TypeError):
            valor_float = 0.0
        
        if pd.isna(valor_float) or np.isnan(valor_float) or np.isinf(valor_float):
            valor_float = 0.0
        features_limpias[col] = valor_float
    return features_limpias


def calcular_edad_meses(fecha_actual_dt, fecha_primera_dt):
    """
    Replica EXACTAMENTE tu fórmula de entrenamiento:
    ((fecha_actual - primera_fecha).days / 30.44).round(1)
    """
    dias = (fecha_actual_dt - fecha_primera_dt).days
    # Si por error de hora la fecha es anterior, devolvemos 0
    if dias < 0: return 0.0
    
    edad_meses = round(dias / 30.44, 1)
    return edad_meses


def calcular_features_historicas_exactas(
    historial_item, 
    historial_previo_item, 
    datos_estaticos, 
    fecha_primera_dt
):
    """
    Calcula features para un punto histórico usando la PRIMERA FECHA como ancla.
    """
    try:
        # 1. Fechas
        fecha_hist = datetime.fromisoformat(historial_item['fecha_calibracion'].replace('Z', '+00:00'))
        
        # 2. Mes
        mes = fecha_hist.month
        
        # 3. Días desde previa (Lógica 'Real' de Colab)
        dias_desde_prev = 0
        if historial_previo_item:
            fecha_prev = datetime.fromisoformat(historial_previo_item['fecha_calibracion'].replace('Z', '+00:00'))
            dias_desde_prev = (fecha_hist - fecha_prev).days
        
        # 4. EDAD OPERACIONAL EN MESES (Tu fórmula)
        edad_operacional = calcular_edad_meses(fecha_hist, fecha_primera_dt)

        # 5. Datos Climáticos
        temp = historial_item.get('temperatura') 
        hum = historial_item.get('humedad')
        if temp is None: temp = datos_estaticos.get('temperatura', 20)
        if hum is None: hum = datos_estaticos.get('humedad', 50)

        # 6. Vector
        features = {
            'marca_id': datos_estaticos.get('marca_id', 0),
            'incertidumbre': datos_estaticos.get('incertidumbre', 0),
            'temperatura': float(temp),
            'humedad': float(hum),
            'num_calibraciones': 0, # Se llenará en el bucle
            'edad_operacional': float(edad_operacional),
            'dias_desde_prev': float(dias_desde_prev),
            'mes': float(mes)
        }
        
        return features, fecha_hist
        
    except Exception as e:
        print(f"⚠️ Error cálculo histórico: {e}")
        return {}, datetime.now()


@bp.route("/buscar", methods=["POST"])
def buscar_instrumento():
    if supabase_service is None:
        return jsonify({'error': 'BD no disponible'}), 503
    
    try:
        data = request.json
        codigo = data.get('codigo', '').strip().upper()
        
        if not codigo: return jsonify({'error': 'Código requerido'}), 400
        
        print(f"\n{'='*60}")
        print(f"🔍 PROCESANDO: {codigo}")
        print(f"{'='*60}")
        
        # 1. Buscar instrumento y obtener historial
        instrumento = supabase_service.buscar_instrumento(codigo)
        if not instrumento: return jsonify({'error': 'Instrumento no encontrado'}), 404
        
        historial_raw = supabase_service.obtener_historial_completo(codigo)
        # ORDENAR (Vital para definir la "Primera Fecha")
        historial = sorted(historial_raw, key=lambda x: x['fecha_calibracion'])
        
        if len(historial) < 1: return jsonify({'error': 'Sin historial'}), 404
        
        # -------------------------------------------------------------------
        # DEFINIR EL ANCLA TEMPORAL (Tu lógica de agregar_variables)
        # -------------------------------------------------------------------
        FECHA_PRIMERA = datetime.fromisoformat(historial[0]['fecha_calibracion'].replace('Z', '+00:00'))
        print(f"✓ Fecha Inicial (Edad 0): {FECHA_PRIMERA.date()}")

        # 2. Obtener datos estáticos y Estado Actual
        features_supa = supabase_service.extraer_features(instrumento, codigo)
        
        # SOBREESCRIBIR EDAD OPERACIONAL CON TU FÓRMULA (MESES)
        # La última calibración en el historial define el estado "actual" para la predicción futura
        fecha_ultima = datetime.fromisoformat(historial[-1]['fecha_calibracion'].replace('Z', '+00:00'))
        edad_actual_meses = calcular_edad_meses(fecha_ultima, FECHA_PRIMERA)
        
        # Actualizamos el diccionario de features con la edad correcta en MESES
        features_supa['edad_operacional'] = edad_actual_meses
        
        features_limpias = limpiar_features(features_supa, feature_cols)
        print(f"✓ Estado Actual -> Fecha: {fecha_ultima.date()} | Edad: {edad_actual_meses} meses")

        # 3. Predicción Futura (Próxima calibración)
        if modelo is None: return jsonify({'error': 'Modelo no cargado'}), 500
        try:
            f_arr = np.array([features_limpias[col] for col in feature_cols]).reshape(1, -1)
            pred_futura = max(1, int(round(modelo.predict(f_arr)[0])))
            fecha_estimada = fecha_ultima + timedelta(days=pred_futura)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
        # 4. RECONSTRUCCIÓN HISTÓRICA
        print(f"\n📊 RECONSTRUYENDO HISTORIA (Escala: Meses / 30.44)")
        print(f"  {'FECHA':<11} | {'DIAS PREV':<10} | {'EDAD (Mes)':<10} | {'PREDICCIÓN'}")
        print(f"  {'-'*11}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
        
        predicciones_historicas = []
        predicciones_historicas.append(0) # El punto 0 siempre es 0

        # Datos estáticos
        datos_estaticos = {
            'marca_id': features_limpias.get('marca_id', 0),
            'incertidumbre': features_limpias.get('incertidumbre', 0),
            'temperatura': features_limpias.get('temperatura', 20),
            'humedad': features_limpias.get('humedad', 50)
        }

        # Iteramos desde el segundo elemento
        for i in range(1, len(historial)):
            try:
                item_actual = historial[i]
                item_previo = historial[i-1]
                
                # Calcular features usando la FECHA_PRIMERA como ancla
                f_hist, fecha_h = calcular_features_historicas_exactas(
                    item_actual,
                    item_previo,
                    datos_estaticos,
                    FECHA_PRIMERA
                )
                
                f_hist['num_calibraciones'] = i + 1
                
                # Limpiar y Predecir
                f_clean = limpiar_features(f_hist, feature_cols)
                f_arr = np.array([f_clean[col] for col in feature_cols]).reshape(1, -1)
                
                raw_pred = modelo.predict(f_arr)[0]
                val_pred = max(1, int(round(raw_pred)))
                
                # LOG
                dias_prev_log = int(f_clean.get('dias_desde_prev', 0))
                edad_log = f"{f_clean.get('edad_operacional', 0):.1f}"
                print(f"  {fecha_h.strftime('%Y-%m-%d'):<11} | {dias_prev_log:<10} | {edad_log:<10} | {val_pred}")
                
                predicciones_historicas.append(val_pred)

            except Exception as e:
                print(f"  [{i}] Error: {e}")
                predicciones_historicas.append(0)

        # 5. Respuesta Final
        response = {
            'instrumento': {
                'codigo': instrumento['codigo'],
                'tipo': instrumento.get('tipo', 'N/A'),
                'marca': instrumento.get('marca', 'N/A'),
                'rango': instrumento.get('rango', 'N/A'),
                'unidad': instrumento.get('unidad', 'N/A'),
                'fecha_calibracion': instrumento['fecha_calibracion'],
                'temperatura': instrumento.get('temperatura'),
                'humedad': instrumento.get('humedad'),
            },
            'prediccion': {
                'dias_hasta_siguiente': pred_futura,
                'meses_aproximados': round(pred_futura / 30.44, 1),
                'semanas_aproximadas': round(pred_futura / 7, 0),
                'fecha_estimada': fecha_estimada.isoformat()
            },
            'historial': [
                {'fecha_calibracion': h['fecha_calibracion'], 'codigo': h['codigo']} 
                for h in historial
            ],
            'predicciones_historicas': predicciones_historicas,
            'features': features_limpias
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@bp.route("/predict", methods=["POST"])
def predict():
    try:
        if modelo is None: return jsonify({'error': 'Modelo no cargado'}), 500
        data = request.json
        features_limpias = limpiar_features(data, feature_cols)
        features_array = np.array([features_limpias[col] for col in feature_cols]).reshape(1, -1)
        pred = modelo.predict(features_array)[0]
        dias = max(1, int(round(pred))) if not pd.isna(pred) else 0
        return jsonify({"dias_hasta_siguiente": dias, "meses_aproximados": round(dias / 30.44, 1)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500