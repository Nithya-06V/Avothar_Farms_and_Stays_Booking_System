import json
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Property(db.Model):
    __tablename__ = "properties"

    id = db.Column(db.Integer, primary_key=True)
    property_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    price_per_night = db.Column(db.Float, nullable=False, default=0.0)
    bedrooms = db.Column(db.Integer, nullable=False, default=1)
    guests = db.Column(db.Integer, nullable=False, default=2)
    facilities = db.Column(db.Text, default="")
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    gallery_images = db.Column(db.Text, default="[]")
    is_available = db.Column(db.Boolean, default=True)
    featured = db.Column(db.Boolean, default=False)
    check_in = db.Column(db.String(20), default="14:00")
    check_out = db.Column(db.String(20), default="12:00")
    max_guests = db.Column(db.Integer, default=6)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def gallery(self):
        raw = self.gallery_images or "[]"
        if isinstance(raw, list):
            return raw
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
        except (TypeError, ValueError):
            pass
        return [self.image_url] if self.image_url else []


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)
    property_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    mobile = db.Column(db.String(30), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)
    property_type = db.Column(db.String(50), nullable=False)
    property_name = db.Column(db.String(150), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    rooms = db.Column(db.Integer, nullable=False)
    special_requests = db.Column(db.Text, default="")
    price_per_night = db.Column(db.Float, nullable=False)
    nights = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="Pending")
    payment_status = db.Column(db.String(30), default="Pending")
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    property = db.relationship("Property", backref=db.backref("bookings", lazy=True))


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(50), db.ForeignKey("bookings.booking_id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="Pending")
    payment_method = db.Column(db.String(50), default="Simulated Payment")
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    booking = db.relationship("Booking", primaryjoin="Payment.booking_id == Booking.booking_id", uselist=False)
