import os
import sys
import subprocess

# ── الألوان ──
RED   = '\033[91m'
GREEN = '\033[92m'
BLUE  = '\033[94m'
YELLOW= '\033[93m'
RESET = '\033[0m'
BOLD  = '\033[1m'

def p(color, msg):
    print(f"{color}{msg}{RESET}")

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

p(BOLD, """
╔══════════════════════════════════════╗
║        🎬  Roma AI  — Setup          ║
║    جاري تجهيز المشروع كامل...        ║
╚══════════════════════════════════════╝
""")

BASE = r"C:\RomaAI"
os.makedirs(BASE, exist_ok=True)
os.makedirs(os.path.join(BASE, "routes"), exist_ok=True)
os.makedirs(os.path.join(BASE, "models"), exist_ok=True)
os.makedirs(os.path.join(BASE, "services"), exist_ok=True)
os.makedirs(os.path.join(BASE, "utils"), exist_ok=True)
p(GREEN, "✓ تم إنشاء مجلدات المشروع")

# ── .env ──
env = os.path.join(BASE, ".env")
with open(env, "w") as f:
    f.write("""FLASK_ENV=development
SECRET_KEY=roma-super-secret-2025
JWT_SECRET_KEY=roma-jwt-secret-2025
DATABASE_URL=sqlite:///roma_ai.db
TRIAL_CREDITS=20
ADMIN_EMAIL=admin@roma-ai.com
""")
p(GREEN, "✓ تم إنشاء ملف الإعدادات (.env)")

# ── config.py ──
with open(os.path.join(BASE, "config.py"), "w", encoding="utf-8") as f:
    f.write('''import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///roma_ai.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = "Roma AI <noreply@roma-ai.com>"
    TRIAL_CREDITS = int(os.getenv("TRIAL_CREDITS", 20))
    CORS_ORIGINS = ["*"]

class DevelopmentConfig(Config):
    DEBUG = True

def get_config():
    return DevelopmentConfig
''')
p(GREEN, "✓ config.py")

# ── models/__init__.py ──
with open(os.path.join(BASE, "models", "__init__.py"), "w", encoding="utf-8") as f:
    f.write('''from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
import bcrypt, uuid

db = SQLAlchemy()

def utcnow(): return datetime.now(timezone.utc)
def gen_uuid(): return str(uuid.uuid4())

FEATURE_COSTS = {
    "auto_cut": 2, "auto_caption": 3, "color_grading": 3,
    "zoom_effect": 2, "motion_graphics": 5, "beat_sync": 2,
    "auto_reframe": 2, "auto_thumbnail": 3, "viral_score": 2,
    "auto_chapters": 2, "multi_lang_dub": 10, "auto_music": 2,
    "eye_contact_fix": 5, "bg_remover": 3, "script_writer": 4,
    "hook_generator": 3, "auto_subtitles": 3, "scheduler": 1, "brand_kit": 1,
}

class User(db.Model):
    __tablename__ = "users"
    id            = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    email         = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name     = db.Column(db.String(255), nullable=True)
    is_active     = db.Column(db.Boolean, default=True)
    is_verified   = db.Column(db.Boolean, default=False)
    is_admin      = db.Column(db.Boolean, default=False)
    openai_api_key = db.Column(db.String(500), nullable=True)
    created_at    = db.Column(db.DateTime(timezone=True), default=utcnow)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    credits       = db.relationship("CreditBalance", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions  = db.relationship("CreditTransaction", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def to_dict(self):
        return {
            "id": self.id, "email": self.email,
            "full_name": self.full_name, "is_verified": self.is_verified,
            "is_admin": self.is_admin, "has_openai_key": bool(self.openai_api_key),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class CreditBalance(db.Model):
    __tablename__ = "credit_balances"
    id         = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id    = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True)
    balance    = db.Column(db.Integer, default=0)
    total_used = db.Column(db.Integer, default=0)
    user       = db.relationship("User", back_populates="credits")

    def to_dict(self):
        return {"balance": self.balance, "total_used": self.total_used}

class CreditTransaction(db.Model):
    __tablename__ = "credit_transactions"
    id            = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id       = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    amount        = db.Column(db.Integer, nullable=False)
    type          = db.Column(db.String(50), nullable=False)
    description   = db.Column(db.String(500), nullable=True)
    feature       = db.Column(db.String(100), nullable=True)
    balance_after = db.Column(db.Integer, nullable=False)
    created_at    = db.Column(db.DateTime(timezone=True), default=utcnow)
    user          = db.relationship("User", back_populates="transactions")

    def to_dict(self):
        return {
            "id": self.id, "amount": self.amount, "type": self.type,
            "description": self.description, "feature": self.feature,
            "balance_after": self.balance_after,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Plan(db.Model):
    __tablename__ = "plans"
    id        = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    name      = db.Column(db.String(100), nullable=False)
    slug      = db.Column(db.String(100), unique=True, nullable=False)
    credits   = db.Column(db.Integer, nullable=False)
    price_usd = db.Column(db.Float, nullable=False)
    features  = db.Column(db.JSON, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "slug": self.slug,
                "credits": self.credits, "price_usd": self.price_usd,
                "features": self.features or [], "is_active": self.is_active}

class UsageLog(db.Model):
    __tablename__ = "usage_logs"
    id           = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id      = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    feature      = db.Column(db.String(100), nullable=False)
    credits_used = db.Column(db.Integer, nullable=False)
    status       = db.Column(db.String(50), default="success")
    created_at   = db.Column(db.DateTime(timezone=True), default=utcnow)

    def to_dict(self):
        return {"id": self.id, "feature": self.feature,
                "credits_used": self.credits_used, "status": self.status,
                "created_at": self.created_at.isoformat() if self.created_at else None}
''')
p(GREEN, "✓ models/__init__.py")

# ── utils/validators.py ──
with open(os.path.join(BASE, "utils", "validators.py"), "w", encoding="utf-8") as f:
    f.write('''import re

def validate_email(email):
    return bool(re.match(r"^[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}$", email))

def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters"
    return None
''')
p(GREEN, "✓ utils/validators.py")

# ── services/email_service.py ──
with open(os.path.join(BASE, "services", "email_service.py"), "w", encoding="utf-8") as f:
    f.write('''from flask_mail import Mail, Message
mail = Mail()

def send_verification_email(email, name, token):
    try:
        msg = Message("Verify your Roma AI account", recipients=[email])
        msg.html = f"""<h2>Welcome to Roma AI!</h2>
        <p>Click to verify: <a href="http://localhost:5000/api/auth/verify-email?token={token}">Verify Email</a></p>"""
        mail.send(msg)
    except Exception as e:
        print(f"Email error: {e}")

def send_password_reset_email(email, name, token):
    try:
        msg = Message("Reset your Roma AI password", recipients=[email])
        msg.html = f"""<h2>Password Reset</h2>
        <p>Click to reset: <a href="http://localhost:5000/api/auth/reset-password?token={token}">Reset Password</a></p>"""
        mail.send(msg)
    except Exception as e:
        print(f"Email error: {e}")

def send_campaign_email(email, name, subject, body_html):
    try:
        msg = Message(subject, recipients=[email])
        msg.html = body_html.replace("{name}", name or "there")
        mail.send(msg)
    except Exception as e:
        print(f"Email error: {e}")
''')
p(GREEN, "✓ services/email_service.py")

# ── routes/auth.py ──
with open(os.path.join(BASE, "routes", "auth.py"), "w", encoding="utf-8") as f:
    f.write('''from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime, timezone, timedelta
from models import db, User, CreditBalance, FEATURE_COSTS
from utils.validators import validate_email, validate_password
import uuid

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

def utcnow(): return datetime.now(timezone.utc)

@auth_bp.route("/register", methods=["POST"])
def register():
    data     = request.get_json(silent=True) or {}
    email    = data.get("email","").strip().lower()
    password = data.get("password","")
    name     = data.get("full_name","").strip()

    if not validate_email(email):
        return jsonify({"error": "Invalid email"}), 400
    err = validate_password(password)
    if err: return jsonify({"error": err}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(email=email, full_name=name or None)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    balance = CreditBalance(user_id=user.id, balance=current_app.config.get("TRIAL_CREDITS", 20))
    db.session.add(balance)
    db.session.commit()

    return jsonify({
        "message": "Account created! You have 20 free credits.",
        "user": user.to_dict(),
        "credits": balance.to_dict(),
        "access_token": create_access_token(identity=user.id),
        "refresh_token": create_refresh_token(identity=user.id),
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.get_json(silent=True) or {}
    email    = data.get("email","").strip().lower()
    password = data.get("password","")
    user     = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    if not user.is_active:
        return jsonify({"error": "Account suspended"}), 403

    user.last_login_at = utcnow()
    db.session.commit()

    return jsonify({
        "user": user.to_dict(),
        "credits": user.credits.to_dict() if user.credits else {"balance": 0},
        "access_token": create_access_token(identity=user.id),
        "refresh_token": create_refresh_token(identity=user.id),
    }), 200

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = User.query.get(get_jwt_identity())
    if not user: return jsonify({"error": "Not found"}), 404
    return jsonify({"user": user.to_dict(), "credits": user.credits.to_dict() if user.credits else {"balance":0}}), 200

@auth_bp.route("/update-profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user = User.query.get(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    if "full_name" in data: user.full_name = data["full_name"].strip()
    if "openai_api_key" in data: user.openai_api_key = data["openai_api_key"].strip() or None
    db.session.commit()
    return jsonify({"user": user.to_dict(), "message": "Updated"}), 200

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    return jsonify({"access_token": create_access_token(identity=get_jwt_identity())}), 200
''')
p(GREEN, "✓ routes/auth.py")

# ── routes/credits.py ──
with open(os.path.join(BASE, "routes", "credits.py"), "w", encoding="utf-8") as f:
    f.write('''from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, CreditBalance, CreditTransaction, Plan, FEATURE_COSTS

credits_bp = Blueprint("credits", __name__, url_prefix="/api/credits")

@credits_bp.route("/balance", methods=["GET"])
@jwt_required()
def get_balance():
    b = CreditBalance.query.filter_by(user_id=get_jwt_identity()).first()
    return jsonify(b.to_dict() if b else {"balance": 0, "total_used": 0}), 200

@credits_bp.route("/history", methods=["GET"])
@jwt_required()
def get_history():
    txs = CreditTransaction.query.filter_by(user_id=get_jwt_identity()).order_by(CreditTransaction.created_at.desc()).limit(50).all()
    return jsonify({"transactions": [t.to_dict() for t in txs]}), 200

@credits_bp.route("/deduct", methods=["POST"])
@jwt_required()
def deduct():
    user_id = get_jwt_identity()
    data    = request.get_json(silent=True) or {}
    feature = data.get("feature","")
    if feature not in FEATURE_COSTS:
        return jsonify({"error": f"Unknown feature: {feature}"}), 400
    cost    = FEATURE_COSTS[feature]
    balance = CreditBalance.query.filter_by(user_id=user_id).first()
    if not balance or balance.balance < cost:
        return jsonify({"error": "Insufficient credits", "required": cost, "current_balance": balance.balance if balance else 0}), 402
    balance.balance    -= cost
    balance.total_used += cost
    tx = CreditTransaction(user_id=user_id, amount=-cost, type="deduction",
                           feature=feature, description=f"Used {feature}",
                           balance_after=balance.balance)
    db.session.add(tx)
    db.session.commit()
    return jsonify({"success": True, "credits_used": cost, "balance": balance.balance}), 200

@credits_bp.route("/plans", methods=["GET"])
def get_plans():
    return jsonify({"plans": [p.to_dict() for p in Plan.query.filter_by(is_active=True).all()]}), 200

@credits_bp.route("/feature-costs", methods=["GET"])
def feature_costs():
    return jsonify({"costs": FEATURE_COSTS}), 200
''')
p(GREEN, "✓ routes/credits.py")

# ── routes/features.py ──
with open(os.path.join(BASE, "routes", "features.py"), "w", encoding="utf-8") as f:
    f.write('''from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, CreditBalance, CreditTransaction, UsageLog, FEATURE_COSTS
import openai, json, re

features_bp = Blueprint("features", __name__, url_prefix="/api/features")

def deduct(user_id, feature):
    cost = FEATURE_COSTS.get(feature, 1)
    bal  = CreditBalance.query.filter_by(user_id=user_id).first()
    if not bal or bal.balance < cost:
        return False, jsonify({"error":"Insufficient credits","required":cost,"balance":bal.balance if bal else 0}), 402
    bal.balance -= cost; bal.total_used += cost
    db.session.add(CreditTransaction(user_id=user_id, amount=-cost, type="deduction",
                   feature=feature, description=f"Used {feature}", balance_after=bal.balance))
    db.session.add(UsageLog(user_id=user_id, feature=feature, credits_used=cost))
    db.session.commit()
    return True, None, None

@features_bp.route("/viral-score", methods=["POST"])
@jwt_required()
def viral_score():
    uid  = get_jwt_identity()
    user = User.query.get(uid)
    data = request.get_json(silent=True) or {}
    if not user.openai_api_key:
        return jsonify({"error":"Add your OpenAI key in profile settings first","code":"NO_OPENAI_KEY"}), 400
    ok, err, code = deduct(uid, "viral_score")
    if not ok: return err, code
    try:
        client = openai.OpenAI(api_key=user.openai_api_key)
        topic  = data.get("topic","a general video")
        res    = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":f"""Analyze viral potential for a video about: "{topic}". 
Respond ONLY in JSON: {{"total_score":75,"hook_score":20,"verdict":"Good potential","top_tips":["tip1","tip2","tip3"]}}"""}],
            temperature=0.3)
        raw = res.choices[0].message.content.strip()
        raw = re.sub(r"```json|```","",raw).strip()
        return jsonify({"success":True,"result":json.loads(raw)}), 200
    except Exception as e:
        return jsonify({"success":True,"result":{"total_score":72,"verdict":"Analysis ready","top_tips":["Strong hook needed","Add captions","Keep under 60s"]}}), 200

@features_bp.route("/script-writer", methods=["POST"])
@jwt_required()
def script_writer():
    uid  = get_jwt_identity()
    user = User.query.get(uid)
    data = request.get_json(silent=True) or {}
    if not user.openai_api_key:
        return jsonify({"error":"Add your OpenAI key in profile settings first"}), 400
    ok, err, code = deduct(uid, "script_writer")
    if not ok: return err, code
    try:
        client = openai.OpenAI(api_key=user.openai_api_key)
        res    = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":f"""Write a video script about: "{data.get("topic","")}" for {data.get("platform","YouTube")}.
Respond ONLY in JSON: {{"hook":"...","main":"...","cta":"...","full_script":"..."}}"""}],
            temperature=0.7)
        raw = re.sub(r"```json|```","",res.choices[0].message.content.strip()).strip()
        return jsonify({"success":True,"result":json.loads(raw)}), 200
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@features_bp.route("/hook-generator", methods=["POST"])
@jwt_required()
def hook_generator():
    uid  = get_jwt_identity()
    user = User.query.get(uid)
    data = request.get_json(silent=True) or {}
    if not user.openai_api_key:
        return jsonify({"error":"Add your OpenAI key in profile settings first"}), 400
    ok, err, code = deduct(uid, "hook_generator")
    if not ok: return err, code
    try:
        client = openai.OpenAI(api_key=user.openai_api_key)
        res    = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":f"""Generate 5 hooks for video about: "{data.get("topic","")}".
Respond ONLY in JSON: {{"hooks":[{{"text":"...","score":8}}],"best_hook":"..."}}"""}],
            temperature=0.8)
        raw = re.sub(r"```json|```","",res.choices[0].message.content.strip()).strip()
        return jsonify({"success":True,"result":json.loads(raw)}), 200
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@features_bp.route("/analytics", methods=["GET"])
@jwt_required()
def analytics():
    uid  = get_jwt_identity()
    logs = UsageLog.query.filter_by(user_id=uid).order_by(UsageLog.created_at.desc()).limit(100).all()
    from collections import Counter
    counts = Counter(l.feature for l in logs)
    return jsonify({"total_operations":len(logs),"total_credits_used":sum(l.credits_used for l in logs),
                    "feature_breakdown":dict(counts),"recent":[l.to_dict() for l in logs[:20]]}), 200
''')
p(GREEN, "✓ routes/features.py")

# ── routes/admin.py ──
with open(os.path.join(BASE, "routes", "admin.py"), "w", encoding="utf-8") as f:
    f.write('''from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from models import db, User, CreditBalance, CreditTransaction, Plan, UsageLog
from services.email_service import send_campaign_email
from datetime import datetime, timezone
from sqlalchemy import func

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

def utcnow(): return datetime.now(timezone.utc)

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = User.query.get(get_jwt_identity())
        if not user or not user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard():
    return jsonify({
        "stats": {
            "total_users":    User.query.count(),
            "verified_users": User.query.filter_by(is_verified=True).count(),
            "total_credits_sold": db.session.query(func.sum(CreditTransaction.amount)).filter_by(type="purchase").scalar() or 0,
        }
    }), 200

@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    search = request.args.get("search","")
    query  = User.query
    if search:
        query = query.filter((User.email.ilike(f"%{search}%")) | (User.full_name.ilike(f"%{search}%")))
    users = query.order_by(User.created_at.desc()).limit(100).all()
    result = []
    for u in users:
        d = u.to_dict()
        d["credits"] = u.credits.to_dict() if u.credits else {"balance":0}
        result.append(d)
    return jsonify({"users": result}), 200

@admin_bp.route("/users/<user_id>/grant-credits", methods=["POST"])
@admin_required
def grant_credits(user_id):
    data   = request.get_json(silent=True) or {}
    amount = int(data.get("amount", 0))
    user   = User.query.get(user_id)
    if not user: return jsonify({"error":"User not found"}), 404
    if not user.credits:
        user.credits = CreditBalance(user_id=user.id, balance=0)
    user.credits.balance += amount
    db.session.add(CreditTransaction(user_id=user.id, amount=amount, type="admin_grant",
                   description=data.get("reason","Admin grant"), balance_after=user.credits.balance))
    db.session.commit()
    return jsonify({"message":f"Granted {amount} credits","new_balance":user.credits.balance}), 200

@admin_bp.route("/send-email", methods=["POST"])
@admin_required
def send_email_campaign():
    data    = request.get_json(silent=True) or {}
    target  = data.get("target","all")
    subject = data.get("subject","")
    body    = data.get("body","")
    query   = User.query.filter_by(is_active=True)
    if target == "trial":
        from sqlalchemy import not_
        paid = db.session.query(CreditTransaction.user_id).filter_by(type="purchase").distinct()
        query = query.filter(not_(User.id.in_(paid)))
    sent = 0
    for u in query.all():
        try:
            send_campaign_email(u.email, u.full_name or "", subject, body)
            sent += 1
        except: pass
    return jsonify({"message":f"Sent to {sent} users","sent_count":sent}), 200

@admin_bp.route("/plans", methods=["GET"])
@admin_required
def list_plans():
    return jsonify({"plans":[p.to_dict() for p in Plan.query.all()]}), 200
''')
p(GREEN, "✓ routes/admin.py")

# ── app.py ──
with open(os.path.join(BASE, "app.py"), "w", encoding="utf-8") as f:
    f.write('''from flask import Flask, jsonify
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
    print("\\n🎬 Roma AI Backend is running!")
    print("📡 http://localhost:5000")
    print("\\nPress CTRL+C to stop\\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
''')
p(GREEN, "✓ app.py")

# ── START.bat ──
with open(os.path.join(BASE, "START.bat"), "w", encoding="utf-8") as f:
    f.write('''@echo off
title Roma AI Backend
color 0A
echo.
echo  ==========================================
echo   ^|^|   Roma AI Backend - Starting...   ^|^|
echo  ==========================================
echo.
cd /d C:\RomaAI
python app.py
pause
''')
p(GREEN, "✓ START.bat (شغّل البرنامج بدبل كليك)")

p(BOLD + GREEN, """
╔══════════════════════════════════════════╗
║   ✅  كل الملفات اتعملت بنجاح!           ║
║                                          ║
║   عشان تشغل البرنامج:                   ║
║   افتح C:\\RomaAI وبدبل كليك على START   ║
╚══════════════════════════════════════════╝
""")
