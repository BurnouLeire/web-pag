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
    Limpia las features reemplazando NaN, None e infinitos con valores seguros.
    """
    features_limpias = {}
    
    for col in feature_cols:
        valor = features_dict.get(col, 0)
        
        # Convertir a float primero
        try:
            valor_float = float(valor) if valor is not None else 0.0
        except (ValueError, TypeError):
            valor_float = 0.0
        
        # Reemplazar NaN e infinitos
        if pd.isna(valor_float) or np.isnan(valor_float):
            valor_float = 0.0
        elif np.isinf(valor_float):
            valor_float = 0.0
        
        features_limpias[col] = valor_float
    
    return features_limpias


def calcular_features_historicas(historial_hasta_punto, codigo):
    """
    Calcula features usando solo el historial disponible hasta cierto punto.
    MANEJA VALORES FALTANTES DE FORMA ROBUSTA.
    """
    try:
        # Si solo hay 1 calibración, usar valores por defecto
        if len(historial_hasta_punto) <= 1:
            features = {
                'dias_desde_ultima': 0,
                'calibraciones_totales': 1,
                'promedio_dias': 0,
                'desv_std_dias': 0,
                'min_dias': 0,
                'max_dias': 0,
                'temperatura': historial_hasta_punto[0].get('temperatura') or 20,
                'humedad': historial_hasta_punto[0].get('humedad') or 50,
                'dias_ultimo_intervalo': 0
            }
            return features
        
        # Calcular intervalos entre calibraciones
        intervalos = []
        for i in range(1, len(historial_hasta_punto)):
            try:
                fecha_actual = datetime.fromisoformat(
                    historial_hasta_punto[i]['fecha_calibracion'].replace('Z', '+00:00')
                )
                fecha_anterior = datetime.fromisoformat(
                    historial_hasta_punto[i-1]['fecha_calibracion'].replace('Z', '+00:00')
                )
                dias = (fecha_actual - fecha_anterior).days
                
                # Validar que el intervalo sea razonable (entre 1 y 3650 días)
                if 1 <= dias <= 3650:
                    intervalos.append(dias)
                    
            except Exception as e:
                print(f"  ⚠️ Error calculando intervalo en índice {i}: {e}")
                continue
        
        # Si no hay intervalos válidos, usar valores por defecto
        if not intervalos:
            intervalos = [0]
        
        # Calcular estadísticas de forma segura
        ultima_calibracion = historial_hasta_punto[-1]
        
        try:
            fecha_ultima = datetime.fromisoformat(
                ultima_calibracion['fecha_calibracion'].replace('Z', '+00:00')
            )
            dias_desde_ultima = max(0, (datetime.now() - fecha_ultima).days)
        except:
            dias_desde_ultima = 0
        
        # Temperatura y humedad con valores por defecto
        temperatura = ultima_calibracion.get('temperatura')
        if temperatura is None or pd.isna(temperatura):
            temperatura = 20
        
        humedad = ultima_calibracion.get('humedad')
        if humedad is None or pd.isna(humedad):
            humedad = 50
        
        # Construir features de forma segura
        features = {
            'dias_desde_ultima': dias_desde_ultima,
            'calibraciones_totales': len(historial_hasta_punto),
            'promedio_dias': float(np.mean(intervalos)),
            'desv_std_dias': float(np.std(intervalos)) if len(intervalos) > 1 else 0.0,
            'min_dias': float(min(intervalos)),
            'max_dias': float(max(intervalos)),
            'temperatura': float(temperatura),
            'humedad': float(humedad),
            'dias_ultimo_intervalo': float(intervalos[-1]) if intervalos else 0.0
        }
        
        # Validar que no haya NaN
        for key, value in features.items():
            if pd.isna(value) or np.isnan(value) or np.isinf(value):
                print(f"  ⚠️ Valor inválido en {key}: {value}, reemplazando con 0")
                features[key] = 0.0
        
        return features
        
    except Exception as e:
        print(f"❌ Error crítico calculando features históricas: {e}")
        import traceback
        traceback.print_exc()
        
        # Retornar features por defecto seguras
        return {
            'dias_desde_ultima': 0.0,
            'calibraciones_totales': 1.0,
            'promedio_dias': 0.0,
            'desv_std_dias': 0.0,
            'min_dias': 0.0,
            'max_dias': 0.0,
            'temperatura': 20.0,
            'humedad': 50.0,
            'dias_ultimo_intervalo': 0.0
        }


@bp.route("/buscar", methods=["POST"])
def buscar_instrumento():
    """Endpoint para buscar instrumento y hacer predicción completa"""
    
    if supabase_service is None:
        return jsonify({
            'error': 'Servicio de base de datos no disponible. Verifica las credenciales en .env'
        }), 503
    
    try:
        data = request.json
        codigo = data.get('codigo', '').strip().upper()
        
        if not codigo:
            return jsonify({'error': 'Código de instrumento requerido'}), 400
        
        print(f"\n{'='*60}")
        print(f"🔍 BUSCANDO INSTRUMENTO: {codigo}")
        print(f"{'='*60}")
        
        # 1. Buscar instrumento en Supabase
        instrumento = supabase_service.buscar_instrumento(codigo)
        if not instrumento:
            return jsonify({'error': f'Instrumento "{codigo}" no encontrado'}), 404
        
        print(f"✓ Instrumento encontrado: {instrumento.get('codigo')}")
        
        # 2. Obtener historial completo (ordenado cronológicamente)
        historial = supabase_service.obtener_historial_completo(codigo)
        print(f"✓ Historial obtenido: {len(historial)} calibraciones")
        
        if len(historial) < 1:
            return jsonify({'error': 'No hay historial de calibraciones para este instrumento'}), 404
        
        # 3. Extraer features del estado actual
        features = supabase_service.extraer_features(instrumento, codigo)
        print(f"✓ Features extraídas (sin limpiar): {features}")
        
        # 4. LIMPIAR FEATURES (eliminar NaN, None, infinitos)
        features_limpias = limpiar_features(features, feature_cols)
        print(f"✓ Features limpias: {features_limpias}")
        
        # 5. Validar que tenemos todas las features necesarias
        features_faltantes = [col for col in feature_cols if col not in features_limpias]
        if features_faltantes:
            print(f"⚠️ Features faltantes: {features_faltantes}")
            return jsonify({'error': f'Features faltantes: {features_faltantes}'}), 400
        
        # 6. Hacer predicción ACTUAL (próxima calibración)
        if modelo is None:
            return jsonify({'error': 'Modelo no cargado'}), 500
        
        try:
            features_array = np.array([features_limpias[col] for col in feature_cols]).reshape(1, -1)
            print(f"✓ Array de features: {features_array}")
            
            prediccion_raw = modelo.predict(features_array)[0]
            print(f"✓ Predicción raw: {prediccion_raw}")
            
            # Validar predicción
            if pd.isna(prediccion_raw) or np.isnan(prediccion_raw) or np.isinf(prediccion_raw):
                print(f"❌ Predicción inválida: {prediccion_raw}")
                return jsonify({'error': 'El modelo generó una predicción inválida (NaN o infinito)'}), 500
            
            dias_predichos = max(1, int(round(prediccion_raw)))  # Mínimo 1 día
            print(f"✓ Predicción final: {dias_predichos} días")
            
        except Exception as e:
            print(f"❌ Error al hacer predicción: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Error al predecir: {str(e)}'}), 500
        
        # 7. Calcular fecha estimada
        try:
            fecha_ultima = datetime.fromisoformat(
                instrumento['fecha_calibracion'].replace('Z', '+00:00')
            )
            fecha_estimada = fecha_ultima + timedelta(days=dias_predichos)
        except Exception as e:
            print(f"❌ Error calculando fecha estimada: {e}")
            fecha_estimada = datetime.now() + timedelta(days=dias_predichos)
        
        # 8. GENERAR PREDICCIONES HISTÓRICAS PARA EL GRÁFICO
        print(f"\n{'='*60}")
        print(f"📊 GENERANDO PREDICCIONES HISTÓRICAS")
        print(f"{'='*60}")
        
        predicciones_historicas = []

        # ✅ PRIMERA CALIBRACIÓN: Siempre 0 (punto de origen)
        predicciones_historicas.append(0)
        print(f"  [1] Primera calibración: 0 días (punto de inicio)")

        # ✅ DESDE LA SEGUNDA CALIBRACIÓN: Empezar a predecir
        for i in range(1, len(historial)):
            try:
                # Obtener solo el historial disponible HASTA este punto
                historial_hasta_aqui = historial[:i+1]
                
                # Calcular features usando SOLO ese historial limitado
                features_hist = calcular_features_historicas(historial_hasta_aqui, codigo)
                
                # Limpiar features históricas
                features_hist_limpias = limpiar_features(features_hist, feature_cols)
                
                # Hacer predicción
                features_hist_array = np.array([features_hist_limpias[col] for col in feature_cols]).reshape(1, -1)
                prediccion_raw = modelo.predict(features_hist_array)[0]
                
                # Validar y convertir
                if pd.isna(prediccion_raw) or np.isnan(prediccion_raw) or np.isinf(prediccion_raw):
                    # Usar promedio de predicciones válidas anteriores
                    predicciones_validas = [p for p in predicciones_historicas if p > 0]
                    prediccion_dias = int(np.mean(predicciones_validas)) if predicciones_validas else 30
                    print(f"  [{i+1}] ⚠️ Predicción inválida, usando promedio: {prediccion_dias} días")
                else:
                    prediccion_dias = max(1, int(round(prediccion_raw)))
                    print(f"  [{i+1}] Calibración {i+1}: {prediccion_dias} días predichos")
                
                predicciones_historicas.append(prediccion_dias)
                
            except Exception as e:
                print(f"  [{i+1}] ❌ Error en calibración {i+1}: {e}")
                
                # Usar promedio de predicciones anteriores válidas
                predicciones_validas = [p for p in predicciones_historicas if p > 0]
                if predicciones_validas:
                    promedio = int(np.mean(predicciones_validas))
                    predicciones_historicas.append(promedio)
                    print(f"  [{i+1}] ⚠️ Usando promedio: {promedio} días")
                else:
                    predicciones_historicas.append(30)  # Valor por defecto razonable
                    print(f"  [{i+1}] ⚠️ Usando valor por defecto: 30 días")

        print(f"\n✓ Predicciones generadas: {len(predicciones_historicas)} valores")
        print(f"  Valores: {predicciones_historicas}")
        print(f"{'='*60}\n")
        
        # 9. Preparar respuesta completa
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
                'dias_hasta_siguiente': dias_predichos,
                'meses_aproximados': round(dias_predichos / 30.44, 1),
                'semanas_aproximadas': round(dias_predichos / 7, 0),
                'fecha_estimada': fecha_estimada.isoformat()
            },
            'historial': [
                {
                    'fecha_calibracion': h['fecha_calibracion'],
                    'codigo': h['codigo']
                } 
                for h in historial
            ],
            'predicciones_historicas': predicciones_historicas,
            'features': features_limpias
        }
        
        print(f"✓ Respuesta preparada exitosamente")
        print(f"  - Historial: {len(response['historial'])} registros")
        print(f"  - Predicciones: {len(response['predicciones_historicas'])} valores")
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO en buscar_instrumento: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500


@bp.route("/predict", methods=["POST"])
def predict():
    """Endpoint simple para predicción (compatible con API directa)"""
    try:
        if modelo is None:
            return jsonify({'error': 'Modelo no cargado'}), 500

        data = request.json
        
        # Validar campos requeridos
        missing = [f for f in feature_cols if f not in data]
        if missing:
            return jsonify({'error': f'Faltan campos: {missing}'}), 400

        # Limpiar features
        features_limpias = limpiar_features(data, feature_cols)
        
        # Hacer predicción
        features_array = np.array([features_limpias[col] for col in feature_cols]).reshape(1, -1)
        pred = modelo.predict(features_array)[0]
        
        # Validar resultado
        if pd.isna(pred) or np.isnan(pred) or np.isinf(pred):
            return jsonify({'error': 'Predicción inválida (NaN o infinito)'}), 500
        
        dias = max(1, int(round(pred)))

        return jsonify({
            "dias_hasta_siguiente": dias,
            "meses_aproximados": round(dias / 30.44, 1)
        })
        
    except Exception as e:
        print(f"Error en predict: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500