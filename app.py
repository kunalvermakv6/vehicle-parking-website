from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database
from model_db import db, Users, ParkingLot, ParkingSpot, Booking
db.init_app(app)

#create the database tables
with app.app_context():
    db.create_all()
    # admin creation
    admin = Users.query.filter_by(role='admin').first()
    if not admin:
        admin = Users(username='admin@01.com', 
                    phone_no='0000000000', 
                    name='Admin', 
                    address='Admin Address', 
                    pincode=123456,
                    password='admin123',
                    role='admin')
        db.session.add(admin)
        db.session.commit()


# Initialize routes
from routes import init_routes
init_routes(app)  # Initialize routes from routes.py


# app run
if __name__ == '__main__':
    app.run(debug=True)
