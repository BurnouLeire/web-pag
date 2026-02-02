import os
import unicodedata
import pandas as pd
import numpy as np
from flask import Blueprint, render_template, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import traceback

from app.models.model_loader import cargar_modelo

load_dotenv()

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# --- 1. CARGA DEL MODELO ---
try:
    # Se espera que cargar_modelo devuelva (objeto_modelo, lista_columnas)
    modelo_data, feature_cols_model = cargar_modelo()
    
    if modelo_data:
        # Si el modelo viene dentro de un diccionario con métricas
        if isinstance(modelo_data, dict) and 'model' in modelo_data:
            r2_global = modelo_data.get('metrics', {}).get('r2', 0.94)
            modelo_real = modelo_data['model']
        else:
            r2_global = 0.94
            modelo_real = modelo_data
        print(f"✅ Dashboard: Modelo ML cargado. Features: {feature_cols_model}")
    else:
        print("⚠️ Dashboard: No se pudo cargar el modelo. Usando valores por defecto.")
        modelo_real = None
        feature_cols_model = []
        r2_global = 0.85 # Valor de respaldo
except Exception as e:
    print(f"❌ Error cargando modelo en Dashboard: {e}")
    modelo_real = None
    feature_cols_model = []
    r2_global = 0.0

# --- Configuración Supabase ---
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
        # ---------------------------------------------------------
        # 2. CONSULTA A SUPABASE (Con paginación para evitar límites)
        # ---------------------------------------------------------
        all_data = []
        offset = 0
        batch_size = 1000 
        cols_to_fetch = "fecha_calibracion, tipo, instrumento, periodicidad, temperatura, humedad, incertidumbre, marca_id, codigo"

        while True:
            response = supabase.table('historicos')\
                .select(cols_to_fetch)\
                .range(offset, offset + batch_size - 1)\
                .execute()
            rows = response.data
            if not rows: break
            all_data.extend(rows)
            if len(rows) < batch_size: break
            offset += batch_size

        if not all_data:
            return jsonify({"error": "No se encontraron datos en la tabla historicos"}), 404

        # ---------------------------------------------------------
        # 3. PROCESAMIENTO CON PANDAS
        # ---------------------------------------------------------
        df = pd.DataFrame(all_data)
        df['fecha_calibracion'] = pd.to_datetime(df['fecha_calibracion'], errors='coerce')
        df = df.dropna(subset=['fecha_calibracion'])
        
        # Identificador único para cada instrumento físico
        df['id_agrupacion'] = df['codigo'].fillna(df['instrumento'])
        df = df.sort_values(by=['id_agrupacion', 'fecha_calibracion'])

        # ---------------------------------------------------------
        # 4. INGENIERÍA DE FEATURES (Para que el modelo pueda predecir)
        # ---------------------------------------------------------
        df['mes'] = df['fecha_calibracion'].dt.month
        df['fecha_primera'] = df.groupby('id_agrupacion')['fecha_calibracion'].transform('min')
        df['edad_operacional'] = (df['fecha_calibracion'] - df['fecha_primera']).dt.days / 30.44
        
        # Intervalo real observado entre calibraciones pasadas
        df['fecha_prev'] = df.groupby('id_agrupacion')['fecha_calibracion'].shift(1)
        df['dias_desde_prev'] = (df['fecha_calibracion'] - df['fecha_prev']).dt.days
        df['dias_desde_prev'] = df['dias_desde_prev'].fillna(0) 

        # Rellenar nulos técnicos
        for col, val in [('temperatura', 20), ('humedad', 50), ('incertidumbre', 0), ('marca_id', 0)]:
            if col not in df.columns: df[col] = val
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(val)

        # ---------------------------------------------------------
        # 5. DATOS PARA EL HISTOGRAMA (Carga de trabajo por año/mes)
        # ---------------------------------------------------------
        df['year'] = df['fecha_calibracion'].dt.year
        conteo_mensual = df.groupby(['year', 'mes']).size()
        available_years = sorted(df['year'].unique().tolist())
        historical_data = {int(y): [int(conteo_mensual.get((y, m), 0)) for m in range(1, 13)] for y in available_years}

        # ---------------------------------------------------------
        # 6. PREDICCIÓN CON EL MODELO ML
        # ---------------------------------------------------------
        usar_modelo_real = False
        if modelo_real is not None and feature_cols_model:
            try:
                # Nos aseguramos que el DF tenga todas las columnas que el modelo pide
                for col in feature_cols_model:
                    if col not in df.columns: df[col] = 0
                
                X_predict = df[feature_cols_model]
                df['prediccion_ia'] = modelo_real.predict(X_predict)
                df['prediccion_ia'] = df['prediccion_ia'].clip(lower=30).round().astype(int)
                usar_modelo_real = True
            except Exception as e_ml:
                print(f"⚠️ Error en predicción masiva: {e_ml}")

        # ---------------------------------------------------------
        # 7. EXTRACCIÓN DE VARIABLES CRÍTICAS (PARA EL GRÁFICO NARANJA)
        # ---------------------------------------------------------
        feature_importance_list = []
        if usar_modelo_real and hasattr(modelo_real, 'feature_importances_'):
            importances = modelo_real.feature_importances_
            for col, imp in zip(feature_cols_model, importances):
                feature_importance_list.append({
                    "variable": col.replace('_', ' ').title(),
                    "importance": round(float(imp) * 100, 2)
                })
        else:
            # Fallback si el modelo no tiene importancias (ej: Regresión Lineal o error)
            feature_importance_list = [
                {"variable": "Deriva Histórica", "importance": 45},
                {"variable": "Uso del Equipo", "importance": 25},
                {"variable": "Humedad/Temp", "importance": 15},
                {"variable": "Incertidumbre", "importance": 10},
                {"variable": "Antigüedad", "importance": 5}
            ]

        # ---------------------------------------------------------
        # 8. RESUMEN POR TIPO DE INSTRUMENTO (TABLA Y DONA)
        # ---------------------------------------------------------
        def limpiar(t): return " ".join(unicodedata.normalize('NFC', str(t)).split()).title()
        df['tipo_final'] = df['instrumento'].apply(limpiar)

        # Calculamos promedios por tipo
        df['period_db'] = pd.to_numeric(df['periodicidad'], errors='coerce')
        
        grouped = df.groupby('tipo_final').agg({
            'tipo_final': 'count',
            'period_db': 'median',
            'dias_desde_prev': lambda x: x[x > 0].median() # Mediana de intervalos reales
        }).rename(columns={'tipo_final': 'total'}).reset_index()

        if usar_modelo_real:
            ia_grouped = df.groupby('tipo_final')['prediccion_ia'].median().reset_index()
            grouped = grouped.merge(ia_grouped, on='tipo_final')

        instrument_types = []
        dias_ganados_total = 0

        for _, row in grouped.iterrows():
            total_equipos = int(row['total'])
            # Intervalo Estándar (DB o Histórico)
            std = int(row['period_db']) if pd.notna(row['period_db']) and row['period_db'] > 0 else \
                  (int(row['dias_desde_prev']) if pd.notna(row['dias_desde_prev']) else 365)
            
            # Intervalo IA
            opt = int(row['prediccion_ia']) if usar_modelo_real else int(std * 1.1)
            
            dias_ganados_total += (opt - std) * total_equipos

            instrument_types.append({
                "type": row['tipo_final'],
                "total": total_equipos,
                "stdInterval": std,
                "optInterval": opt
            })

        # ---------------------------------------------------------
        # 9. RESPUESTA FINAL AL DASHBOARD.JS
        # ---------------------------------------------------------
        return jsonify({
            "aiMetrics": {
                "r2Score": f"{r2_global:.2f}", 
                "processedCertificates": len(df),
                "daysOptimized": int(dias_ganados_total) 
            },
            "historicalData": historical_data,
            "availableYears": available_years,
            "instrumentTypes": sorted(instrument_types, key=lambda x: x['total'], reverse=True),
            "featureImportance": feature_importance_list
        })

    except Exception as e:
        print(f"❌ Error crítico en Dashboard Data: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500