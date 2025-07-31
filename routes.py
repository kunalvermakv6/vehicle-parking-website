from datetime import datetime,timedelta,timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash,session
from model_db import db, Users, ParkingLot, ParkingSpot, Booking
from sqlalchemy import func,and_
from sqlalchemy.orm import joinedload

def init_routes(app):
    
    def auth_required(f):
        """Decorator to check if user is logged in."""
        @wraps(f)
        def inner(*args, **kwargs):
            if 'user_id' not in session:
                flash('You need to log in first.', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return inner
    
    
    # Routes for the application

    # Welcome
    @app.route('/')
    def home():
        return render_template('welcome.html')


    # Login
    @app.route('/login')
    def login():
        return render_template('login.html')

    @app.route('/login', methods=['POST'])
    def login_post():
        username = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(username=username).first()
        if not user:
            flash('User not found, please try again.', 'danger')
            return redirect(url_for('home'))
        if not user.check_password(password):
            flash('Incorrect password, please try again.', 'danger')
            return redirect(url_for('login'))
        
        flash('Login successful!', 'success')
        session['user_id']= user.id
        return redirect(url_for('dashboard', username=username))
    

    # Logout
    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('You have been logged out.', 'success')
        return redirect(url_for('home'))


    # registration
    @app.route('/register')
    def register():
        return render_template('register.html')
    
    @app.route('/register',methods=['POST'])
    def register_post():
        username = request.form.get('email')
        password = request.form.get('password')
        phone_no = request.form.get('phone_no')
        full_name = request.form.get('full_name')
        address = request.form.get('address')
        pincode = request.form.get('pincode')

        if Users.query.filter_by(username=username).first():
            flash('Username already exists, please choose a different one.', 'danger')
            return redirect(url_for('login'))
        user= Users(username = username, 
                    phone_no = phone_no, 
                    name = full_name, 
                    address = address, 
                    pincode = pincode,
                    password = password,
                    role = 'user')
        db.session.add(user)
        db.session.commit() 
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))



    # Routes for user dashboard and related pages
    @app.route('/<username>/dashboard', methods=['GET'])
    @auth_required
    def dashboard(username):
        user = Users.query.get(session['user_id'])
        today = datetime.now().strftime('%A, %d %B %Y ')
        

        if user.role == 'admin':
            # Dropdown logic
            selected_lot_id = request.args.get('lot_id', type=int)
            parking_lots = ParkingLot.query.all()

            if not selected_lot_id and parking_lots:
                selected_lot_id = parking_lots[0].id

            parking_spots = ParkingSpot.query.filter_by(lot_id=selected_lot_id).all()

            # Statistics
            closed_spots = ParkingSpot.query.filter_by(status='closed').count()
            available_spots = ParkingSpot.query.filter_by(status='available').count()
            total_spots = ParkingSpot.query.count()
            total_lots = len(parking_lots)

            return render_template('admin/dashboard.html',
                                username=username,
                                user=user,
                                today=today,
                                parking_lots=parking_lots,
                                selected_lot_id=selected_lot_id,
                                parking_spots=parking_spots,
                                total_lots=total_lots,
                                total_spots=total_spots,
                                closed_spots=closed_spots,
                                available_spots=available_spots)
        else:
            bookings = Booking.query.options(joinedload(Booking.spot).joinedload(ParkingSpot.lot)).filter_by(user_id=session['user_id']).all()
            for booking in bookings:
                if booking.start_time and booking.end_time:
                    delta = booking.end_time - booking.start_time  # this is a timedelta object
                    booking.duration_hours = round(delta.total_seconds() / 3600, 2)
                else:
                    booking.duration_hours = 0 

            near=ParkingLot.query.filter(ParkingLot.pincode==user.pincode).limit(2).all()
            active_bookings = Booking.query.filter(datetime.now() < Booking.end_time).all()

            #
            completed_bookings = Booking.query.filter(
                Booking.end_time <= datetime.now(),
                Booking.Early_pickup == 0
            ).all()

            for booking in completed_bookings:
                spot = ParkingSpot.query.get(booking.spot_id)

                if spot and spot.status == "occupied":
                    # Check if any newer booking exists on the same spot
                    future_booking_exists = Booking.query.filter(
                        and_(
                            Booking.spot_id == spot.id,
                            Booking.start_time > booking.end_time
                        )
                    ).first()

                    # Only free the spot if no future booking exists
                    if not future_booking_exists:
                        spot.status = "available"

            db.session.commit()
            return render_template('user/dashboard.html',
                                    username=username,
                                    user=user,
                                    today=today,
                                    Bookings=bookings,
                                    datetime=datetime,
                                    near=near,
                                    active_bookings=active_bookings)



    @app.route('/<username>/profile')
    @auth_required
    def profile(username):
        user = Users.query.get(session['user_id'])
        return render_template('user/profile.html', username=username, user=user)
    
    @app.route('/<username>/edit-profile', methods=['POST'])
    @auth_required
    def edit_profile(username):
        user = Users.query.filter_by(username=username).first_or_404()
        
        npassword = request.form.get('npassword')
        cpassword = request.form.get('cpassword')

        if not cpassword or not user.check_password(cpassword):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for('profile', username=username))

        user.name = request.form.get('full_name')
        user.phone_no = request.form.get('phone_no')
        user.pincode = request.form.get('pincode')
        user.address = request.form.get('address')

        if len(npassword) >= 6:
            user.password = request.form.get('npassword')
        elif npassword:
            flash("New password must be at least 6 characters.", "danger")
            return redirect(url_for('dashboard', username=username))

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for('profile', username=username))


    @app.route('/user/book')
    @auth_required
    def book():
        user = Users.query.get(session['user_id'])
        return render_template('user/book.html', user=user)


    @app.route('/<username>/summary')
    @auth_required
    def summary(username):
        user = Users.query.get(session['user_id'])

        if user.role == 'admin':
            # Grouping slots by status for chart
            slot_status_data = (
                db.session.query(ParkingSpot.status, func.count(ParkingSpot.id))
                .group_by(ParkingSpot.status)
                .all()
            )

            status_labels = [status for status, count in slot_status_data]
            status_counts = [count for status, count in slot_status_data]

            revenues = db.session.query(
                ParkingLot.name,
                func.sum(
                    func.strftime('%s', Booking.end_time) - func.strftime('%s', Booking.start_time)
                ).label('total_seconds'),
                ParkingLot.price_per_hrs
            ).join(ParkingSpot, ParkingLot.id == ParkingSpot.lot_id)\
            .join(Booking, Booking.spot_id == ParkingSpot.id)\
            .group_by(ParkingLot.id).all()

            lot_names = []
            lot_revenues = []

            for name, total_seconds, price_per_hr in revenues:
                total_hours = total_seconds / 3600 if total_seconds else 0
                revenue = round(total_hours * price_per_hr, 2)
                lot_names.append(name)
                lot_revenues.append(revenue)

            # Render appropriate summary template based on role
        
            return render_template('admin/summary.html',
                                username=username,
                                user=user,
                                status_labels=status_labels,
                                status_counts=status_counts,
                                lot_names=lot_names,
                                lot_revenues=lot_revenues)
        else:
            bookings = Booking.query.options(joinedload(Booking.spot).joinedload(ParkingSpot.lot)).filter_by(user_id=session['user_id']).all()
            total_booking=len(bookings)
            total_hours = 0
            user_spending=0
            for booking in bookings:
                duration = booking.end_time - booking.start_time  # this gives timedelta
                dur=int(duration.total_seconds() / 3600)
                total_hours += int(duration.total_seconds() / 3600)    # convert seconds to hours
                spot = ParkingSpot.query.get(booking.spot_id)
                if spot:
                    cost = int(duration.total_seconds() / 3600) * spot.price_per_hrs
                    user_spending += cost
            return render_template('user/summary.html',
                                username=username,
                                user=user,
                                bookings=bookings,
                                total_booking=total_booking,
                                total_hours=total_hours,
                                user_spending=user_spending,
                                dur=dur)


    @app.route('/admin/search')
    def admin_search():
        username = "admin"
        return render_template('admin/search.html', username=username)
    
    # specials
    #admin dashboard add parking Lot modal
    @app.route('/<username>/parking-lot/add', methods=['POST'])
    @auth_required
    def add_lot(username):
        name = request.form.get('name')
        address = request.form.get('address')
        total_spots = request.form.get('total_spots')
        pincode = request.form.get('pincode')
        status = request.form.get('status')
        price_per_hr = request.form.get('price_per_hr')

        if ParkingLot.query.filter_by(name=name).first():
            flash('Parking lot name already exists, please choose a different name.', 'danger')
            return redirect(url_for('summary', username=username))
        lot= ParkingLot(name = name, 
                    address = address, 
                    total_spots = int(total_spots),  
                    pincode = pincode,
                    status = status,
                    admin_id= session['user_id'],
                    price_per_hrs= price_per_hr)
        db.session.add(lot)
        db.session.commit() 

        for i in range(1, int(total_spots) + 1):
            spot = ParkingSpot(
                lot_id=lot.id,
                status='available' if lot.status == 'active' else 'closed',
                type='regular',  # or customize later
                price_per_hrs= price_per_hr  # default price, change as needed
            )
            db.session.add(spot)

        db.session.commit()
        flash('Parking lot added successfully! ', 'success')
        return redirect(url_for('dashboard', username=username))
    
    #admin dashboard edit parking lot modal
    @app.route('/<username>/update-lot', methods=['POST'])
    @auth_required
    def update_lot(username):
        lot_id = request.form.get('parkingId')
        name = request.form.get('name')
        address = request.form.get('Address')
        pincode = request.form.get('pincode')
        status = request.form.get('status')
        price_per_hr = request.form.get('price')


        lot = ParkingLot.query.get(lot_id)
        spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()

        if not lot:
            flash("Parking lot not found.", "danger")
            return redirect(url_for('dashboard', username=username))

        #  Check if a different lot already has the same name
        existing_lot = ParkingLot.query.filter(ParkingLot.name == name, ParkingLot.id != lot_id).first()
        if existing_lot:
            flash("Parking lot name already exists. Please choose a different name.", "danger")
            return redirect(url_for('dashboard', username=username))

        #  Update fields
        lot.name = name
        lot.address = address
        lot.pincode = pincode
        lot.status = status
        lot.price_per_hrs = price_per_hr
        if lot.status == 'active':
            for spot in spots:
                spot.status = 'available'
        elif lot.status == 'closed':
            for spot in spots:
                spot.status = 'closed'
        
        db.session.commit()
        flash("Parking lot updated successfully!", "success")
        return redirect(url_for('dashboard', username=username))
    
    #admin dashboard delete parking lot modal
    @app.route('/<username>/delete-lot/<int:lot_id>', methods=['POST'])
    @auth_required
    def delete_lot(username, lot_id):
        lot = ParkingLot.query.get(lot_id)
        spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
        if not lot:
            flash("Parking lot not found.", "danger")
            return redirect(url_for('dashboard', username=username))
        
        # Delete all associated parking spots
        for spot in spots:
            db.session.delete(spot)
        
        db.session.delete(lot)
        db.session.commit()
        flash("Lot deleted successfully.", "success")
        return redirect(url_for('dashboard', username=username))

    @app.route('/<username>/user_details')
    @auth_required
    def admin_user_details(username):
        current_user = Users.query.get(session['user_id'])

        if current_user.role != 'admin':
            flash('You do not have permission to view this page.', 'danger')
            return redirect(url_for('home'))

        users = Users.query.filter(Users.role == 'user').all()
        total_users = len(users)
        occupied_count = ParkingSpot.query.filter_by(status='occupied').count()
        closed_count=ParkingSpot.query.filter_by(status='closed').count()
        return render_template('admin/user-details.html',
                            username=username,
                            current_user=current_user,
                            users=users,
                            total_user=total_users,
                            occupied_count=occupied_count,
                            closed_count=closed_count)
    
    # Add a new parking slot to a lot
    @app.route('/<username>/add-slot', methods=['POST'])
    @auth_required
    def add_slot(username):
        lot_id = request.form.get('lotId')
        slot_price = request.form.get('slotprice')
        slot_type = request.form.get('slotType')
        status = request.form.get('slotStatus')

        lot = ParkingLot.query.get(lot_id)

        if not lot:
            flash("Parking lot not found.", "danger")
            return redirect(url_for('dashboard', username=username))

        new_slot = ParkingSpot(
            lot_id=lot_id,
            type=slot_type,
            price_per_hrs=slot_price,
            status=status
        )
        db.session.add(new_slot)
        lot.total_spots += 1
        db.session.commit()
        flash("Parking slot added successfully!", "success")
        return redirect(url_for('dashboard', username=username))
    
    @app.route('/<username>/edit-slot/<int:slot_id>', methods=['GET', 'POST'])
    @auth_required
    def edit_slot(username, slot_id):
        slot = ParkingSpot.query.get(slot_id)
        if not slot:
            flash("Slot not found.", "danger")
            return redirect(url_for('dashboard', username=username))

        if request.method == 'POST':
            # Get updated values from form
            slot.type = request.form.get('slotType')
            slot.status = request.form.get('slotStatus')
            slot.price_per_hrs = request.form.get('slotPrice')
            
            db.session.commit()
            flash("Slot updated successfully!", "success")
            return redirect(url_for('dashboard', username=username))
        
        return render_template('admin/edit_slot.html', username=username, slot=slot)

    #search parking lots
    @app.route('/<username>/search-lots', methods=['GET'])
    @auth_required 
    def search_Lots(username):
        user = Users.query.get(session['user_id'])
        lot_id = request.args.get('lotId')
        name = request.args.get('name')
        location = request.args.get('location')
        status = request.args.get('status')
        min_capacity = request.args.get('capacity')
        price_range = request.args.get('priceRange')

        query = ParkingLot.query

        if lot_id:
            query = query.filter(ParkingLot.id.like(f"%{lot_id}%"))
        if name:
            query = query.filter(ParkingLot.name.ilike(f"%{name}%"))
        if location:
            query = query.filter(ParkingLot.address.ilike(f"%{location}%"))
        if status and status != "Any Status":
            query = query.filter_by(status=status)
        if min_capacity:
            try:
                query = query.filter(ParkingLot.total_spots >= int(min_capacity))
            except ValueError:
                pass
        if price_range and price_range != "Any Price":
            try:
                low, high = map(int, price_range.split('-'))
                query = query.filter(ParkingLot.price_per_hrs.between(low, high))
            except ValueError:
                pass


        lots = query.all()
        return render_template('admin/search.html',
                            username=username,parking_lots=lots)


    @app.route('/<username>/update-slot', methods=['POST'])
    @auth_required
    def update_slot(username):
        slot_id = request.form.get('slotId')
        slot_type = request.form.get('slotType')
        slot_status = request.form.get('slotStatus')
        slot_price = request.form.get('slotPrice')

        slot = ParkingSpot.query.get(slot_id)

        if not slot:
            flash("Slot not found.", "danger")
            return redirect(url_for('dashboard', username=username))

        # Update values
        slot.type = slot_type
        slot.status = slot_status
        slot.price_per_hrs = slot_price

        db.session.commit()
        flash("Slot updated successfully.", "success")
        return redirect(url_for('dashboard', username=username))

    #book now 
    @app.route('/<username>/booking' ,methods=['POST','GET'])
    @auth_required
    def book_now(username):
        if request.method == 'POST':
            spot_id = request.form.get('spot_id')
            vehicle_no = request.form.get('vehicle_no')
            duration_hours = int(request.form.get('duration_hours'))

            user_id = session.get('user_id')
            if not user_id:
                flash("Please login to book a spot.", "danger")
                return redirect(url_for('login'))

            # Check if the spot exists and is available
            spot = ParkingSpot.query.get(spot_id)
            if not spot or not (spot.status=="available"):
                flash("Selected parking spot is not available.", "danger")
                return redirect(url_for('dashboard', username=username))

            start_time = datetime.now(timezone.utc)+ timedelta(hours=5 ,minutes=30)
            end_time = start_time + timedelta(hours=duration_hours)

            # Create new booking
            booking = Booking(
                user_id=user_id,
                spot_id=spot_id,
                vehicle_no=vehicle_no,
                start_time=start_time,
                end_time=end_time
            )

            spot.status = "occupied"  # Update spot availability
            db.session.add(spot)
            db.session.add(booking)
            db.session.commit()

            flash("Parking spot successfully booked!", "success")
            return redirect(url_for('dashboard', username=username))

        # GET request
        spots = ParkingSpot.query.filter_by(status="available").all()
        return render_template('user/book_now.html', username=username, spots=spots)
    
    @app.route('/release-booking/<int:booking_id>/<int:spot_id>', methods=['POST'])
    @auth_required
    def release_booking(booking_id, spot_id):
        booking = Booking.query.get(booking_id)
        spot = ParkingSpot.query.get(spot_id)

        if booking and spot:
            booking.Early_pickup = 1
            booking.end_time = datetime.utcnow() + timedelta(hours=5,minutes=30) # end booking now
            spot.status = 'available'

            db.session.commit()
            flash('Booking released successfully.', 'success')
        else:
            flash('Invalid booking or spot.', 'danger')

        return redirect(request.referrer or url_for('dashboard'))
    

    @app.route('/<username>/find' )
    @auth_required
    def find(username):
        lot_id = request.args.get('lotId')
        name = request.args.get('name')
        location = request.args.get('location')
        status = request.args.get('status')
        pincode = request.args.get('pincode')
        price_range = request.args.get('priceRange')

        query = ParkingLot.query.filter_by(status='active')

        if lot_id:
            query = query.filter(ParkingLot.id.like(f"%{lot_id}%"))
        if name:
            query = query.filter(ParkingLot.name.ilike(f"%{name}%"))
        if location:
            query = query.filter(ParkingLot.address.ilike(f"%{location}%"))
        if status and status != "Any Status":
            query = query.filter_by(status=status)
        if pincode:
            query = query.filter(ParkingLot.pincode.like(f"%{pincode}%"))
        
        if price_range and price_range != "Any Price":
            try:
                low, high = map(int, price_range.split('-'))
                query = query.filter(ParkingLot.price_per_hrs.between(low, high))
            except ValueError:
                pass


        parking_lots = query.all()
        
        return render_template('user/find.html',username=username,parking_lots=parking_lots)