from flask import Blueprint, request, jsonify
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
