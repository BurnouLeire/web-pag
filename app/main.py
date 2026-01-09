# app/main.py
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

def create_app():
    load_dotenv()
    app = Flask(__name__)
    CORS(app)

    # ESTO ES LO NUEVO: Hace que las llaves sean globales en los HTML
    @app.context_processor
    def inject_supabase_creds():
        return dict(
            supabase_url=os.getenv('SUPABASE_URL'),
            supabase_key=os.getenv('SUPABASE_KEY')
        )

    from app.routes import auth, dashboard, laboratorio, api
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(laboratorio.bp)
    app.register_blueprint(api.bp)
    
    return app