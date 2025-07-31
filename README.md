#  Vehicle Parking App – V1

A web-based vehicle parking management system built using **Flask**, **SQLite**, **Jinja2**,**Bootstrap** and **TailwindCSS**. The system supports **Admin** and **User** roles for managing and booking parking lots and slots with live status updates.

---

##  Features

###  User Functionality:
- Register/Login
- View available parking lots
- Reserve a parking spot
- Early pickup option
- View active and past bookings
- Automatic release after end time

###  Admin Functionality:
- Login as Admin
- Create, update, and delete parking lots
- View and manage all users
- Filter and search parking lots
- Dashboard with summary statistics

---

##  Project Structure

vehicle_parking_app/
│
├── app.py # Main application entry point
├── models.py # SQLAlchemy models
├── templates/ # HTML (Jinja2) templates
│ ├── admin/
│ ├── user/
│ └── auth/
├── static/ # Static assets (CSS/JS/images)
├── instance/ # SQLite databases (auto-generated)
├── requirements.txt # Required Python packages
└── README.md # This file

---

##  Tech Stack

- **Backend**: Flask, SQLAlchemy
- **Frontend**: Jinja2 (HTML), bootstrap,TailwindCSS
- **Database**: SQLite
- **Styling**: TailwindCSS + some custom CSS
- **Authentication**: Session-based login (Admin/User)
- **Date/Time Handling**: `datetime` module

---

##  How to Run the App Locally

### 1. Clone the repository

### 2. Create virtual environment and install dependencies

### 3. Run the application

---
## Testing Credentials
### Admin Login:
Username: admin@01.com
Password: admin123

### User Login
Username: user1@example.com
Password: user123
