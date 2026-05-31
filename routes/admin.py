from flask import Blueprint, request, jsonify
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
