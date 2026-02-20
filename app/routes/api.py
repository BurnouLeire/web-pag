from flask import Blueprint, request, jsonify
from app.services.prediction_service import PredictionService

bp = Blueprint("api", __name__, url_prefix="/api")

# Instanciamos el servicio una sola vez (carga el modelo al iniciar)
prediction_service = PredictionService()

@bp.post("/predict")
def predict():
    try:
        data = request.json
        
        # Delegamos la lógica de validación, limpieza y predicción al servicio
        dias, meses = prediction_service.predict_single(data)

        return jsonify({
            "dias_hasta_siguiente": dias,
            "meses_aproximados": meses
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500