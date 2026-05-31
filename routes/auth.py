from flask import Blueprint, request, jsonify, current_app
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
