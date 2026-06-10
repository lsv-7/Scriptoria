import os
from flask import Flask, jsonify
from flask_cors import CORS

from backend.config import Config
from backend.routes.auth_routes import auth_bp
from backend.routes.project_routes import project_bp
from backend.routes.story_routes import story_bp
from backend.routes.screenplay_routes import screenplay_bp
from backend.routes.character_routes import character_bp
from backend.routes.scene_routes import scene_bp
from backend.routes.storyboard_routes import storyboard_bp
from backend.routes.sound_routes import sound_bp
from backend.routes.production_routes import production_bp
from backend.routes.export_routes import export_bp
from backend.routes.budget_routes import budget_bp

def create_app():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_dir = os.path.join(root_dir, "frontend")
    
    app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
    app.config.from_object(Config)

    # Enable CORS for all routes (to support running frontend locally)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Root route to serve static frontend index
    @app.route("/", methods=["GET"])
    def serve_index():
        return app.send_static_file("index.html")

    # Register blueprints (with no url prefix to match exact API endpoint definitions)
    app.register_blueprint(auth_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(story_bp)
    app.register_blueprint(screenplay_bp)
    app.register_blueprint(character_bp)
    app.register_blueprint(scene_bp)
    app.register_blueprint(storyboard_bp)
    app.register_blueprint(sound_bp)
    app.register_blueprint(production_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(budget_bp)

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            "status": "error",
            "message": "The requested API endpoint was not found on this server."
        }), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "status": "error",
            "message": "An internal server error occurred.",
            "details": str(error)
        }), 500

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "online",
            "system": "CineForge AI Backend",
            "timestamp": os.getenv("FLASK_ENV", "development")
        }), 200

    return app

app = create_app()

if __name__ == "__main__":
    # Retrieve port from config
    port = Config.PORT
    print(f"CineForge AI Server starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
