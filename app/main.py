from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

def create_app():
    # Cargar variables de entorno
    load_dotenv()
    
    app = Flask(__name__)
    
    # Habilitar CORS
    CORS(app)
    
    # Importar y registrar blueprints
    from app.routes import auth, dashboard, laboratorio, api
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(laboratorio.bp)
    app.register_blueprint(api.bp)
    
    return app