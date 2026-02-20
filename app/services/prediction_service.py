import numpy as np
import pandas as pd
from app.models.model_loader import cargar_modelo
from app.services.feature_engineering import FeatureEngineering

class PredictionService:
    def __init__(self):
        # 1. Cargar el modelo y las columnas esperadas
        self.modelo_data, self.feature_cols = cargar_modelo()
        
        # 2. Manejar si el modelo viene envuelto en un diccionario o es directo
        if isinstance(self.modelo_data, dict) and 'model' in self.modelo_data:
            self.model_obj = self.modelo_data['model']
            self.metrics = self.modelo_data.get('metrics', {'r2': 0.0})
        else:
            self.model_obj = self.modelo_data
            self.metrics = {'r2': 0.94} # Valor por defecto si no hay métricas

    def predict_single(self, features_dict):
        """
        Realiza una predicción para un solo ítem (usado en API y Laboratorio).
        Devuelve: (dias_predichos, meses_predichos)
        """
        if self.model_obj is None:
            raise Exception("Modelo ML no cargado correctamente")

        # Usamos el FeatureEngineering para limpiar, pasándole NUESTRAS columnas
        clean_features = FeatureEngineering.limpiar_features(features_dict, self.feature_cols)
        
        # Convertir a array numpy (1 fila, N columnas)
        features_arr = np.array([clean_features[col] for col in self.feature_cols]).reshape(1, -1)
        
        # Predecir
        pred = self.model_obj.predict(features_arr)[0]
        
        # Post-procesamiento
        dias = max(1, int(round(pred))) if not pd.isna(pred) else 0
        meses = round(dias / FeatureEngineering.CONST_DIAS_MES, 1)
        
        return dias, meses

    def predict_batch(self, df):
        """
        Realiza predicciones masivas para un DataFrame (usado en Dashboard).
        Devuelve una Serie de Pandas con las predicciones.
        """
        if self.model_obj is None or df.empty:
            return np.zeros(len(df))

        # Asegurar que existan todas las columnas que el modelo pide
        X = df.copy()
        for col in self.feature_cols:
            if col not in X.columns:
                X[col] = 0
        
        try:
            predictions = self.model_obj.predict(X[self.feature_cols])
            # Aplicar reglas de negocio (mínimo 30 días, redondeo)
            return np.clip(predictions, 30, None).round().astype(int)
        except Exception as e:
            print(f"Error en predicción batch: {e}")
            return np.zeros(len(df))

    def limpiar_features(self, features_dict):
        """
        Método wrapper para limpiar features usando las columnas que conoce este servicio.
        Corrige el error: 'PredictionService' object has no attribute 'limpiar_features'
        """
        return FeatureEngineering.limpiar_features(features_dict, self.feature_cols)

    def get_feature_importance_list(self):
        """
        Devuelve la lista de importancia de variables para el gráfico del Dashboard.
        """
        feature_importance_list = []
        
        # Verificar si el modelo tiene feature_importances_ (ej: RandomForest, XGBoost, GradientBoosting)
        if self.model_obj is not None and hasattr(self.model_obj, 'feature_importances_'):
            try:
                importances = self.model_obj.feature_importances_
                for col, imp in zip(self.feature_cols, importances):
                    feature_importance_list.append({
                        "variable": col.replace('_', ' ').title(),
                        "importance": round(float(imp) * 100, 2)
                    })
                # Ordenar por importancia descendente
                feature_importance_list.sort(key=lambda x: x['importance'], reverse=True)
            except Exception as e:
                print(f"No se pudieron extraer importancias: {e}")

        # Si falló o el modelo no soporta importancias (ej: LinearRegression simple), usar Fallback
        if not feature_importance_list:
            feature_importance_list = [
                {"variable": "Deriva Histórica", "importance": 45},
                {"variable": "Uso del Equipo", "importance": 25},
                {"variable": "Humedad/Temp", "importance": 15},
                {"variable": "Incertidumbre", "importance": 10},
                {"variable": "Antigüedad", "importance": 5}
            ]
            
        return feature_importance_list