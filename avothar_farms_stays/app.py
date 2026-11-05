import csv
import json
import os
from datetime import datetime, timedelta
from io import BytesIO, StringIO

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from config import Config
from init_db import init_database
from models import Admin, Booking, Payment, Property, Review, User, db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        init_database(app)

    @app.context_processor
    def inject_globals():
        return {"current_year": datetime.utcnow().year}

    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/")
    def index():
        featured_properties = Property.query.filter_by(featured=True).limit(6).all()
        reviews = Review.query.order_by(Review.created_at.desc()).limit(3).all()
        stats = {
            "total_properties": Property.query.count(),
            "total_bookings": Booking.query.count(),
        }
        return render_template("index.html", properties=featured_properties, reviews=reviews, stats=stats)

    @app.route("/properties")
    def properties():
        property_type = request.args.get("type", "all")
        query = Property.query
        if property_type and property_type.lower() != "all":
            query = query.filter(Property.property_type.ilike(property_type))
        properties_list = query.order_by(Property.created_at.desc()).all()
        return render_template("properties.html", properties=properties_list, selected_type=property_type)

    @app.route("/property/<int:property_id>")
    def property_details(property_id):
        property = Property.query.get_or_404(property_id)
        similar = Property.query.filter(
            Property.id != property.id,
            Property.property_type == property.property_type,
        ).limit(3).all()
        return render_template("property_details.html", property=property, similar=similar)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            admin = Admin.query.filter_by(username=username).first()
            if admin and check_password_hash(admin.password_hash, password):
                session["admin_logged_in"] = True
                session["admin_id"] = admin.id
                flash("Welcome back, Admin!", "success")
                return redirect(url_for("admin_dashboard"))
            flash("Invalid username or password. Please try again.", "danger")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out successfully.", "success")
        return redirect(url_for("index"))

    @app.route("/dashboard")
    def dashboard():
        status_filter = request.args.get("status", "All")
        from_date = request.args.get("date_from")
        to_date = request.args.get("date_to")

        query = Booking.query
        if status_filter and status_filter != "All":
            query = query.filter(Booking.status == status_filter)
        if from_date:
            query = query.filter(Booking.check_in >= datetime.strptime(from_date, "%Y-%m-%d").date())
        if to_date:
            query = query.filter(Booking.check_out <= datetime.strptime(to_date, "%Y-%m-%d").date())

        bookings = query.order_by(Booking.created_at.desc()).all()
        upcoming = Booking.query.filter(Booking.check_in >= datetime.utcnow().date(), Booking.status != "Cancelled").count()
        total_revenue = sum(b.total_amount for b in Booking.query.filter(Booking.status != "Cancelled").all())

        stats = {
            "total_bookings": Booking.query.count(),
            "upcoming_bookings": upcoming,
            "completed_bookings": Booking.query.filter_by(status="Completed").count(),
            "cancelled_bookings": Booking.query.filter_by(status="Cancelled").count(),
            "total_revenue": total_revenue,
        }
        return render_template("dashboard.html", bookings=bookings, stats=stats, status_filter=status_filter)

    @app.route("/booking-history")
    def booking_history():
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        return render_template("booking_history.html", bookings=bookings)

    @app.route("/booking/<int:property_id>", methods=["GET", "POST"])
    def booking(property_id):
        property = Property.query.get_or_404(property_id)

        if request.method == "POST":
            customer_name = (request.form.get("customer_name") or "").strip()
            email = (request.form.get("email") or "").strip()
            mobile = (request.form.get("mobile") or "").strip()
            check_in_text = request.form.get("check_in")
            check_out_text = request.form.get("check_out")
            guests = int(request.form.get("guests") or 0)
            rooms = int(request.form.get("rooms") or 0)
            special_requests = (request.form.get("special_requests") or "").strip()

            if not all([customer_name, email, mobile, check_in_text, check_out_text]):
                flash("Please complete all required booking details.", "danger")
                return render_template("booking.html", property=property)

            if guests <= 0 or rooms <= 0:
                flash("Guests and rooms must be greater than zero.", "danger")
                return render_template("booking.html", property=property)

            try:
                check_in = datetime.strptime(check_in_text, "%Y-%m-%d").date()
                check_out = datetime.strptime(check_out_text, "%Y-%m-%d").date()
            except ValueError:
                flash("Please provide valid check-in and check-out dates.", "danger")
                return render_template("booking.html", property=property)

            if check_out <= check_in:
                flash("Check-out date must be after the check-in date.", "danger")
                return render_template("booking.html", property=property)

            nights = (check_out - check_in).days
            total_amount = property.price_per_night * nights * rooms

            existing_booking = Booking.query.filter(
                Booking.property_id == property.id,
                Booking.status != "Cancelled",
                Booking.check_in < check_out,
                Booking.check_out > check_in,
            ).first()
            if existing_booking:
                flash("This property is already booked for the selected dates. Please choose another date range.", "danger")
                return render_template("booking.html", property=property)

            booking_id = generate_booking_id()
            while Booking.query.filter_by(booking_id=booking_id).first():
                booking_id = generate_booking_id()

            booking = Booking(
                booking_id=booking_id,
                customer_name=customer_name,
                email=email,
                mobile=mobile,
                property_id=property.id,
                property_type=property.property_type,
                property_name=property.name,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                rooms=rooms,
                special_requests=special_requests,
                price_per_night=property.price_per_night,
                nights=nights,
                total_amount=total_amount,
                status="Pending",
                payment_status="Pending",
            )
            db.session.add(booking)
            db.session.commit()

            payment = Payment(booking_id=booking_id, amount=total_amount, status="Pending")
            db.session.add(payment)
            db.session.commit()

            flash("Booking created successfully. Please review your confirmation below.", "success")
            return redirect(url_for("booking_success", booking_id=booking_id))

        return render_template("booking.html", property=property)

    @app.route("/booking-success/<booking_id>")
    def booking_success(booking_id):
        booking = Booking.query.filter_by(booking_id=booking_id).first_or_404()
        return render_template("booking_success.html", booking=booking)

    @app.route("/receipt/<booking_id>")
    def download_receipt(booking_id):
        booking = Booking.query.filter_by(booking_id=booking_id).first_or_404()
        os.makedirs(app.config["RECEIPT_FOLDER"], exist_ok=True)
        file_path = os.path.join(app.config["RECEIPT_FOLDER"], f"{booking_id}.pdf")

        pdf = canvas.Canvas(file_path, pagesize=A4)
        pdf.setTitle(f"Receipt for {booking.booking_id}")
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(50, 780, "Avothar Farms & Stays")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, 760, "Booking Receipt")
        pdf.drawString(50, 735, f"Booking ID: {booking.booking_id}")
        pdf.drawString(50, 710, f"Customer: {booking.customer_name}")
        pdf.drawString(50, 685, f"Email: {booking.email}")
        pdf.drawString(50, 660, f"Phone: {booking.mobile}")
        pdf.drawString(50, 635, f"Property: {booking.property_name}")
        pdf.drawString(50, 610, f"Property Type: {booking.property_type}")
        pdf.drawString(50, 585, f"Check-in: {booking.check_in}")
        pdf.drawString(50, 560, f"Check-out: {booking.check_out}")
        pdf.drawString(50, 535, f"Nights: {booking.nights}")
        pdf.drawString(50, 510, f"Rooms: {booking.rooms}")
        pdf.drawString(50, 485, f"Guests: {booking.guests}")
        pdf.drawString(50, 460, f"Rate per Night: ₹{booking.price_per_night:,.0f}")
        pdf.drawString(50, 435, f"Total Amount: ₹{booking.total_amount:,.0f}")
        pdf.drawString(50, 410, f"Status: {booking.status}")
        pdf.drawString(50, 385, "Thank you for choosing Avothar Farms & Stays.")
        pdf.save()

        return send_file(file_path, as_attachment=True, download_name=f"{booking_id}.pdf")

    @app.route("/admin")
    def admin_redirect():
        if session.get("admin_logged_in"):
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("login"))

    @app.route("/admin/dashboard")
    def admin_dashboard():
        if not session.get("admin_logged_in"):
            flash("Please log in to access the admin dashboard.", "warning")
            return redirect(url_for("login"))

        bookings = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()
        stats = {
            "total_properties": Property.query.count(),
            "total_villas": Property.query.filter_by(property_type="Villa").count(),
            "total_farmhouses": Property.query.filter_by(property_type="Farmhouse").count(),
            "total_houses": Property.query.filter_by(property_type="House").count(),
            "total_bookings": Booking.query.count(),
            "pending_bookings": Booking.query.filter_by(status="Pending").count(),
            "confirmed_bookings": Booking.query.filter_by(status="Confirmed").count(),
            "total_revenue": sum(b.total_amount for b in Booking.query.filter(Booking.status != "Cancelled").all()),
        }
        return render_template("admin_dashboard.html", bookings=bookings, stats=stats)

    @app.route("/admin/properties")
    def manage_properties():
        if not session.get("admin_logged_in"):
            flash("Please log in to manage properties.", "warning")
            return redirect(url_for("login"))
        properties_list = Property.query.order_by(Property.created_at.desc()).all()
        return render_template("manage_properties.html", properties=properties_list)

    @app.route("/admin/properties/add", methods=["GET", "POST"])
    def add_property():
        if not session.get("admin_logged_in"):
            flash("Please log in to add properties.", "warning")
            return redirect(url_for("login"))

        if request.method == "POST":
            image_url = (request.form.get("image_url") or "").strip()
            image_file = request.files.get("image_file")
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                image_file.save(path)
                image_url = url_for("uploaded_file", filename=filename, _external=True)

            gallery_text = request.form.get("gallery_images") or ""
            gallery_items = [item.strip() for item in gallery_text.splitlines() if item.strip()]
            if image_url and not gallery_items:
                gallery_items = [image_url]

            property = Property(
                property_type=request.form.get("property_type"),
                name=(request.form.get("name") or "").strip(),
                location=(request.form.get("location") or "").strip(),
                price_per_night=float(request.form.get("price_per_night") or 0),
                bedrooms=int(request.form.get("bedrooms") or 1),
                guests=int(request.form.get("guests") or 2),
                facilities=(request.form.get("facilities") or "").strip(),
                description=(request.form.get("description") or "").strip(),
                image_url=image_url or "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80",
                gallery_images=json.dumps(gallery_items),
                is_available=request.form.get("is_available") == "on",
                featured=request.form.get("featured") == "on",
                check_in=request.form.get("check_in") or "14:00",
                check_out=request.form.get("check_out") or "12:00",
                max_guests=int(request.form.get("max_guests") or 6),
            )
            db.session.add(property)
            db.session.commit()
            flash("Property added successfully.", "success")
            return redirect(url_for("manage_properties"))

        return render_template("add_property.html")

    @app.route("/admin/properties/edit/<int:property_id>", methods=["GET", "POST"])
    def edit_property(property_id):
        if not session.get("admin_logged_in"):
            flash("Please log in to edit properties.", "warning")
            return redirect(url_for("login"))

        property = Property.query.get_or_404(property_id)
        if request.method == "POST":
            image_url = (request.form.get("image_url") or "").strip()
            image_file = request.files.get("image_file")
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                image_file.save(path)
                image_url = url_for("uploaded_file", filename=filename, _external=True)

            gallery_text = request.form.get("gallery_images") or ""
            gallery_items = [item.strip() for item in gallery_text.splitlines() if item.strip()]
            if image_url and not gallery_items:
                gallery_items = [image_url]

            property.property_type = request.form.get("property_type")
            property.name = (request.form.get("name") or "").strip()
            property.location = (request.form.get("location") or "").strip()
            property.price_per_night = float(request.form.get("price_per_night") or 0)
            property.bedrooms = int(request.form.get("bedrooms") or 1)
            property.guests = int(request.form.get("guests") or 2)
            property.facilities = (request.form.get("facilities") or "").strip()
            property.description = (request.form.get("description") or "").strip()
            property.image_url = image_url or property.image_url
            property.gallery_images = json.dumps(gallery_items)
            property.is_available = request.form.get("is_available") == "on"
            property.featured = request.form.get("featured") == "on"
            property.check_in = request.form.get("check_in") or property.check_in
            property.check_out = request.form.get("check_out") or property.check_out
            property.max_guests = int(request.form.get("max_guests") or property.max_guests)
            db.session.commit()
            flash("Property updated successfully.", "success")
            return redirect(url_for("manage_properties"))

        return render_template("edit_property.html", property=property)

    @app.route("/admin/properties/delete/<int:property_id>", methods=["POST"])
    def delete_property(property_id):
        if not session.get("admin_logged_in"):
            flash("Please log in to delete properties.", "warning")
            return redirect(url_for("login"))
        property = Property.query.get_or_404(property_id)
        db.session.delete(property)
        db.session.commit()
        flash("Property deleted successfully.", "success")
        return redirect(url_for("manage_properties"))

    @app.route("/admin/bookings", methods=["GET", "POST"])
    def manage_bookings():
        if not session.get("admin_logged_in"):
            flash("Please log in to manage bookings.", "warning")
            return redirect(url_for("login"))

        if request.method == "POST":
            booking_id = request.form.get("booking_id")
            new_status = request.form.get("status")
            booking = Booking.query.filter_by(booking_id=booking_id).first_or_404()
            booking.status = new_status
            if new_status in ["Confirmed", "Completed"]:
                booking.payment_status = "Paid"
            elif new_status == "Cancelled":
                booking.payment_status = "Failed"
            else:
                booking.payment_status = "Pending"
            db.session.commit()
            flash("Booking status updated successfully.", "success")

        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        return render_template("manage_bookings.html", bookings=bookings)

    @app.route("/admin/reports")
    def reports():
        if not session.get("admin_logged_in"):
            flash("Please log in to view reports.", "warning")
            return redirect(url_for("login"))

        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        total_revenue = sum(b.total_amount for b in bookings if b.status != "Cancelled")
        stats = {
            "total_bookings": len(bookings),
            "confirmed": sum(1 for b in bookings if b.status == "Confirmed"),
            "pending": sum(1 for b in bookings if b.status == "Pending"),
            "cancelled": sum(1 for b in bookings if b.status == "Cancelled"),
            "revenue": total_revenue,
        }
        return render_template("reports.html", bookings=bookings, stats=stats)

    @app.route("/admin/reports/download")
    def download_reports():
        if not session.get("admin_logged_in"):
            flash("Please log in to download reports.", "warning")
            return redirect(url_for("login"))

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Booking ID", "Customer Name", "Property", "Status", "Total Amount", "Check-In", "Check-Out"])
        for booking in Booking.query.order_by(Booking.created_at.desc()).all():
            writer.writerow([
                booking.booking_id,
                booking.customer_name,
                booking.property_name,
                booking.status,
                booking.total_amount,
                booking.check_in,
                booking.check_out,
            ])

        output.seek(0)
        csv_data = output.getvalue().encode("utf-8")
        return send_file(
            BytesIO(csv_data),
            as_attachment=True,
            download_name="avothar_booking_report.csv",
            mimetype="text/csv",
        )

    return app


def generate_booking_id():
    now = datetime.utcnow()
    random_part = os.urandom(2).hex().upper()
    return f"AVT-{now.strftime('%Y%m%d')}-{random_part}"


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
