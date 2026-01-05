import pickle
import os

FEATURE_COLS = [
    'incertidumbre',
    'temperatura',
    'humedad',
    'marca_id',
    'num_calibraciones',
    'edad_operacional',
    'dias_desde_prev',
    'mes'
]

def cargar_modelo():
    model_path = os.path.join(
        os.path.dirname(__file__),
        'modelo_regresion.pkl'
    )

    try:
        with open(model_path, "rb") as f:
            modelo_data = pickle.load(f)

        if isinstance(modelo_data, dict):
            modelo = modelo_data['model']
            feature_cols = modelo_data.get('feature_cols', FEATURE_COLS)
        else:
            modelo = modelo_data
            feature_cols = FEATURE_COLS

        return modelo, feature_cols

    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return None, FEATURE_COLS
