from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class SupabaseService:
    def __init__(self):
        # Debug: mostrar lo que encuentra
        print(f"DEBUG - SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
        print(f"DEBUG - SUPABASE_KEY existe: {bool(os.getenv('SUPABASE_KEY'))}")
        
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError(
                f"Credenciales de Supabase no configuradas.\n"
                f"URL encontrada: {bool(self.url)}\n"
                f"KEY encontrada: {bool(self.key)}\n"
                f"Verifica que el archivo .env existe en la raíz del proyecto."
            )
        
        self.client: Client = create_client(self.url, self.key)
        print("✓ Supabase conectado exitosamente")
    
    def buscar_instrumento(self, codigo: str) -> Optional[Dict]:
        """Obtiene la última calibración de un instrumento"""
        try:
            response = self.client.table('historicos') \
                .select('*') \
                .eq('codigo', codigo) \
                .order('fecha_calibracion', desc=True) \
                .limit(1) \
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error al buscar instrumento: {e}")
            return None
    
    def obtener_historial_completo(self, codigo: str) -> List[Dict]:
        """Obtiene todo el historial de calibraciones"""
        try:
            response = self.client.table('historicos') \
                .select('*') \
                .eq('codigo', codigo) \
                .order('fecha_calibracion', desc=False) \
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"Error al obtener historial: {e}")
            return []
    
    def extraer_features(self, instrumento: Dict, codigo: str) -> Dict:
        """Extrae las features necesarias para el modelo"""
        try:
            # Obtener historial completo
            historial = self.obtener_historial_completo(codigo)
            
            if not historial:
                raise ValueError("No se encontró historial para el instrumento")
            
            # 1. Número de calibraciones
            num_calibraciones = len(historial)
            
            # 2. Edad operacional (meses desde primera calibración)
            fecha_primera = datetime.fromisoformat(historial[0]['fecha_calibracion'].replace('Z', '+00:00'))
            fecha_actual = datetime.fromisoformat(instrumento['fecha_calibracion'].replace('Z', '+00:00'))
            edad_operacional = round((fecha_actual - fecha_primera).days / 30.44, 1)
            
            # 3. Días desde calibración anterior
            dias_desde_prev = 0
            if len(historial) > 1:
                fecha_prev = datetime.fromisoformat(historial[-2]['fecha_calibracion'].replace('Z', '+00:00'))
                dias_desde_prev = (fecha_actual - fecha_prev).days
            
            # 4. Extraer valores con defaults
            incertidumbre = float(instrumento.get('incertidumbre') or 0.0)
            temperatura = float(instrumento.get('temperatura') or 22.0)
            humedad = float(instrumento.get('humedad') or 60.0)
            marca_id = int(instrumento.get('marca_id') or 0)
            mes = fecha_actual.month
            
            features = {
                'incertidumbre': incertidumbre,
                'temperatura': temperatura,
                'humedad': humedad,
                'marca_id': marca_id,
                'num_calibraciones': num_calibraciones,
                'edad_operacional': edad_operacional,
                'dias_desde_prev': dias_desde_prev,
                'mes': mes
            }
            
            print(f"Features extraídas: {features}")
            return features
            
        except Exception as e:
            print(f"Error al extraer features: {e}")
            raise
    
    def extraer_features_hasta_indice(self, instrumento: Dict, codigo: str, indice: int, historial_completo: List[Dict]) -> Dict:
        """Extrae features usando solo el historial hasta un índice específico"""
        try:
            # Usar solo el historial hasta ese índice (inclusive)
            historial_limitado = historial_completo[:indice + 1]
            
            if not historial_limitado:
                raise ValueError("No hay historial disponible para el índice especificado")
            
            # 1. Número de calibraciones hasta ese punto
            num_calibraciones = len(historial_limitado)
            
            # 2. Edad operacional (meses desde primera calibración hasta esta)
            fecha_primera = datetime.fromisoformat(historial_limitado[0]['fecha_calibracion'].replace('Z', '+00:00'))
            fecha_actual = datetime.fromisoformat(instrumento['fecha_calibracion'].replace('Z', '+00:00'))
            edad_operacional = round((fecha_actual - fecha_primera).days / 30.44, 1)
            
            # 3. Días desde calibración anterior
            dias_desde_prev = 0
            if len(historial_limitado) > 1:
                fecha_prev = datetime.fromisoformat(historial_limitado[-2]['fecha_calibracion'].replace('Z', '+00:00'))
                dias_desde_prev = (fecha_actual - fecha_prev).days
            
            # 4. Extraer valores con defaults
            incertidumbre = float(instrumento.get('incertidumbre') or 0.0)
            temperatura = float(instrumento.get('temperatura') or 22.0)
            humedad = float(instrumento.get('humedad') or 60.0)
            marca_id = int(instrumento.get('marca_id') or 0)
            mes = fecha_actual.month
            
            features = {
                'incertidumbre': incertidumbre,
                'temperatura': temperatura,
                'humedad': humedad,
                'marca_id': marca_id,
                'num_calibraciones': num_calibraciones,
                'edad_operacional': edad_operacional,
                'dias_desde_prev': dias_desde_prev,
                'mes': mes
            }
            
            return features
            
        except Exception as e:
            print(f"Error al extraer features hasta índice: {e}")
            raise
