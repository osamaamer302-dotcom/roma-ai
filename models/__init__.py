from datetime import datetime, timezone
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
