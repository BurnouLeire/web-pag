import pandas as pd
import numpy as np
from datetime import datetime

class FeatureEngineering:
    CONST_DIAS_MES = 30.44

    @staticmethod
    def parsear_fecha(fecha_str):
        """
        Convierte una fecha string (ISO) de Supabase a objeto datetime.
        Maneja el sufijo 'Z' para compatibilidad.
        """
        if not fecha_str:
            return None
        try:
            # Reemplazamos Z por +00:00 para que fromisoformat no falle en versiones viejas de Python
            return datetime.fromisoformat(str(fecha_str).replace('Z', '+00:00'))
        except (ValueError, TypeError):
            print(f"Error parseando fecha: {fecha_str}")
            return datetime.now()

    @staticmethod
    def limpiar_features(features_dict, feature_cols):
        """
        Limpia un diccionario de features asegurando tipos float y quitando infinitos.
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

    @staticmethod
    def calcular_edad_meses(fecha_actual_dt, fecha_primera_dt):
        """
        Calcula la edad operacional en meses.
        """
        if not fecha_primera_dt or not fecha_actual_dt:
            return 0.0
        
        dias = (fecha_actual_dt - fecha_primera_dt).days
        if dias < 0: return 0.0
        
        return round(dias / FeatureEngineering.CONST_DIAS_MES, 1)

    @staticmethod
    def calcular_features_historicas(item_actual, item_previo, datos_estaticos, fecha_primera_dt):
        """
        Calcula el vector de características para un punto histórico específico.
        Usado en el bucle de reconstrucción de laboratorio.
        """
        # 1. Parsear fechas usando el método propio
        fecha_hist = FeatureEngineering.parsear_fecha(item_actual['fecha_calibracion'])
        
        # 2. Calcular días desde previo
        dias_desde_prev = 0
        if item_previo:
            fecha_prev = FeatureEngineering.parsear_fecha(item_previo['fecha_calibracion'])
            dias_desde_prev = (fecha_hist - fecha_prev).days
        
        # 3. Edad Operacional
        edad_operacional = FeatureEngineering.calcular_edad_meses(fecha_hist, fecha_primera_dt)

        # 4. Datos Climáticos (con fallback a estáticos)
        temp = item_actual.get('temperatura') 
        hum = item_actual.get('humedad')
        
        if temp is None: temp = datos_estaticos.get('temperatura', 20)
        if hum is None: hum = datos_estaticos.get('humedad', 50)

        # 5. Construir diccionario
        features = {
            'marca_id': datos_estaticos.get('marca_id', 0),
            'incertidumbre': datos_estaticos.get('incertidumbre', 0),
            'temperatura': float(temp) if temp is not None else 20.0,
            'humedad': float(hum) if hum is not None else 50.0,
            'edad_operacional': float(edad_operacional),
            'dias_desde_prev': float(dias_desde_prev),
            'mes': float(fecha_hist.month)
        }
        
        return features, fecha_hist

    @staticmethod
    def preparar_dataframe_dashboard(data_list):
        """
        Procesa la lista de diccionarios de Supabase y devuelve un DataFrame listo para predecir.
        """
        if not data_list:
            return pd.DataFrame()

        df = pd.DataFrame(data_list)
        
        # 1. Fechas
        df['fecha_calibracion'] = pd.to_datetime(df['fecha_calibracion'], errors='coerce')
        df = df.dropna(subset=['fecha_calibracion'])
        
        # Identificador único
        df['id_agrupacion'] = df['codigo'].fillna(df['instrumento'])
        df = df.sort_values(by=['id_agrupacion', 'fecha_calibracion'])

        # 2. Feature Engineering masivo
        df['mes'] = df['fecha_calibracion'].dt.month
        df['fecha_primera'] = df.groupby('id_agrupacion')['fecha_calibracion'].transform('min')
        df['edad_operacional'] = (df['fecha_calibracion'] - df['fecha_primera']).dt.days / FeatureEngineering.CONST_DIAS_MES
        
        df['fecha_prev'] = df.groupby('id_agrupacion')['fecha_calibracion'].shift(1)
        df['dias_desde_prev'] = (df['fecha_calibracion'] - df['fecha_prev']).dt.days
        df['dias_desde_prev'] = df['dias_desde_prev'].fillna(0)

        # Rellenar nulos
        defaults = [('temperatura', 20), ('humedad', 50), ('incertidumbre', 0), ('marca_id', 0)]
        for col, val in defaults:
            if col not in df.columns: df[col] = val
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(val)

        return df

    @staticmethod
    def agrupar_por_tipo(df, usar_ia=False):
        """
        Genera el resumen por tipo de instrumento para el dashboard.
        """
        import unicodedata
        
        def limpiar_nombre(t): 
            return " ".join(unicodedata.normalize('NFC', str(t)).split()).title()

        if df.empty: return []

        df['tipo_final'] = df['instrumento'].apply(limpiar_nombre)
        df['period_db'] = pd.to_numeric(df['periodicidad'], errors='coerce')

        # Agrupación base
        aggs = {
            'tipo_final': 'count',
            'period_db': 'median',
            'dias_desde_prev': lambda x: x[x > 0].median()
        }
        
        grouped = df.groupby('tipo_final').agg(aggs).rename(columns={'tipo_final': 'total'}).reset_index()

        # Si hay predicciones de IA, agregamos su mediana
        if 'prediccion_ia' in df.columns:
            ia_grouped = df.groupby('tipo_final')['prediccion_ia'].median().reset_index()
            grouped = grouped.merge(ia_grouped, on='tipo_final', how='left')

        instrument_types = []
        for _, row in grouped.iterrows():
            total = int(row['total'])
            std = int(row['period_db']) if pd.notna(row['period_db']) and row['period_db'] > 0 else \
                  (int(row['dias_desde_prev']) if pd.notna(row['dias_desde_prev']) else 365)
            
            # Si existe prediccion_ia, usarla, sino +10%
            opt = int(row['prediccion_ia']) if 'prediccion_ia' in row and pd.notna(row['prediccion_ia']) else int(std * 1.1)

            instrument_types.append({
                "type": row['tipo_final'],
                "total": total,
                "stdInterval": std,
                "optInterval": opt
            })
            
        return sorted(instrument_types, key=lambda x: x['total'], reverse=True)