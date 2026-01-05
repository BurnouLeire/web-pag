from flask import Blueprint, request, jsonify
import numpy as np
from app.models.model_loader import cargar_modelo

bp = Blueprint("api", __name__, url_prefix="/api")

modelo, feature_cols = cargar_modelo()

@bp.post("/predict")
def predict():
    if modelo is None:
        return jsonify({'error': 'Modelo no cargado'}), 500

    data = request.json

    missing = [f for f in feature_cols if f not in data]
    if missing:
        return jsonify({'error': f'Faltan campos: {missing}'}), 400

    features = np.array(
        [float(data[f]) for f in feature_cols]
    ).reshape(1, -1)

    pred = modelo.predict(features)[0]

    return jsonify({
        "dias_hasta_siguiente": round(float(pred), 2),
        "meses_aproximados": round(float(pred) / 30.44, 1)
    })
