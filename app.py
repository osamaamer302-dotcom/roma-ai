from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import get_config
from models import db
from services.email_service import mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())
    db.init_app(app)
    mail.init_app(app)
    JWTManager(app)
    CORS(app)

    from routes.auth     import auth_bp
    from routes.credits  import credits_bp
    from routes.features import features_bp
    from routes.admin    import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(credits_bp)
    app.register_blueprint(features_bp)
    app.register_blueprint(admin_bp)

    @app.route("/api/health")
    def health():
        return jsonify({"status":"ok","service":"Roma AI"}), 200

    @app.errorhandler(404)
    def not_found(e): return jsonify({"error":"Not found"}), 404

    @app.errorhandler(500)
    def server_error(e): return jsonify({"error":"Server error"}), 500

    with app.app_context():
        db.create_all()
        _seed()
    return app

def _seed():
    from models import Plan
    plans = [
        {"name":"Starter","slug":"starter","credits":100,"price_usd":9.99,"features":["Auto Cut","Auto Caption","Color Grading","Beat Sync"]},
        {"name":"Pro","slug":"pro","credits":300,"price_usd":24.99,"features":["All Starter","Script Writer","Viral Score","Hook Generator","Motion Graphics"]},
        {"name":"Agency","slug":"agency","credits":1000,"price_usd":69.99,"features":["All Pro","Multi Language Dub","Eye Contact Fix","Scheduler","Priority Support"]},
    ]
    for p in plans:
        if not Plan.query.filter_by(slug=p["slug"]).first():
            db.session.add(Plan(**p))
    db.session.commit()

if __name__ == "__main__":
    app = create_app()
    print("\n🎬 Roma AI Backend is running!")
    print("📡 http://localhost:5000")
    print("\nPress CTRL+C to stop\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
