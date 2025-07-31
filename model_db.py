from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

# -----------------------------
# USERS TABLE
# -----------------------------
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    passhash = db.Column(db.String(512), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200))
    pincode = db.Column(db.Integer)
    role = db.Column(db.String(10))  # e.g., 'admin' or 'user'
    phone_no = db.Column(db.String(10))

    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)
    parking_lots = db.relationship('ParkingLot', backref='admin', lazy=True)

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute")
    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)
    
    # Password hashing methods
    def check_password(self, password):
        return check_password_hash(self.passhash, password)
# -----------------------------
# PARKING LOT TABLE
# -----------------------------
class ParkingLot(db.Model):
    __tablename__ = 'parking_lot'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_spots = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(200))
    pincode = db.Column(db.Integer)
    status = db.Column(db.String(10))  # 'active', 'inactive', etc.
    price_per_hrs = db.Column(db.Integer)

    # Relationships
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True)

# -----------------------------
# PARKING SPOT TABLE
# -----------------------------
class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(20), nullable=True)  # e.g., 'available', 'booked'
    type = db.Column(db.String(20), nullable=True)  # e.g., 'regular', 'premium'
    price_per_hrs = db.Column(db.Integer)

    # Relationships
    bookings = db.relationship('Booking', backref='spot', lazy=True)

# -----------------------------
# BOOKINGS TABLE
# -----------------------------
class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    vehicle_no = db.Column(db.String(50))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    Early_pickup = db.Column(db.Boolean, default=False)
