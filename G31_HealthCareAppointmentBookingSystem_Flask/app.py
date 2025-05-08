# Standard library imports
import os
import logging
from datetime import timedelta, datetime
from logging.handlers import RotatingFileHandler
from functools import wraps
from random import choice

# Third-party imports
from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_restful import Api, Resource
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

# Flask configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "doccure.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-jwt-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
app.config['JWT_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['JWT_COOKIE_CSRF_PROTECT'] = True

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
api = Api(app)

# Update CORS configuration for Django frontend
CORS(app, 
     supports_credentials=True, 
     resources={r"/api/*": {
         "origins": ["http://localhost:8000", "http://localhost:5000", "https://yourdjangoapp.com"],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"],
         "expose_headers": ["Content-Type", "Authorization"]
     }})

# Create upload folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Models
class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=True)
    is_super_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(50), nullable=False, default="admin")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_super_admin': self.is_super_admin,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=True, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    profile_image = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'profile_image': self.profile_image,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Doctor(db.Model, UserMixin):
    __tablename__ = "doctors"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(50), nullable=True, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.Integer)
    city = db.Column(db.String(50))
    fees = db.Column(db.Float, nullable=False)
    profile_image = db.Column(db.String(200))
    role = db.Column(db.String(50), nullable=False, default="doctor")
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_available = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Float, default=0.0)
    total_ratings = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'email': self.email,
            'specialization': self.specialization,
            'experience': self.experience,
            'city': self.city,
            'fees': self.fees,
            'profile_image': self.profile_image,
            'role': self.role,
            'is_available': self.is_available,
            'rating': self.rating,
            'total_ratings': self.total_ratings,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(20), nullable=False)
    illness = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Confirmed')
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)
    prescription = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)

    def to_dict(self):
        return {
            'id': self.id,
            'service_id': self.service_id,
            'doctor_id': self.doctor_id,
            'patient_id': self.patient_id,
            'appointment_date': self.appointment_date.strftime('%Y-%m-%d'),
            'time_slot': self.time_slot,
            'illness': self.illness,
            'status': self.status,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'contact': self.contact,
            'age': self.age,
            'gender': self.gender,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'notes': self.notes,
            'prescription': self.prescription,
            'follow_up_date': self.follow_up_date.strftime('%Y-%m-%d') if self.follow_up_date else None
        }

# API Resources
class LoginResource(Resource):
    def post(self):
        try:
            data = request.get_json()
            if not data:
                return {'status': 'error', 'message': 'No data provided'}, 400

            # Validate required fields
            required_fields = ['email', 'password']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return {'status': 'error', 'message': f'Missing required fields: {", ".join(missing_fields)}'}, 400

            email = data.get('email')
            password = data.get('password')
            
            # First try to find user as admin
            user = Admin.query.filter_by(email=email).first()
            
            # If not found as admin, check if they're a doctor
            if not user:
                user = Doctor.query.filter_by(email=email).first()
            
            # If still not found, check if they're a patient
            if not user:
                user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                access_token = create_access_token(identity=str(user.id))
                return {
                    'status': 'success',
                    'access_token': access_token,
                    'token_type': 'Bearer',
                    'user': user.to_dict()
                }, 200
            
            return {'status': 'error', 'message': 'Invalid credentials'}, 401

        except Exception as e:
            app.logger.error(f'Login error: {str(e)}')
            return {'status': 'error', 'message': 'Error processing login request'}, 500

class RegisterResource(Resource):
    def post(self):
        try:
            data = request.get_json()
            if not data:
                return {'status': 'error', 'message': 'No data provided'}, 400

            # Validate required fields
            required_fields = ['email', 'password', 'full_name']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return {'status': 'error', 'message': f'Missing required fields: {", ".join(missing_fields)}'}, 400

            # Extract and validate data
            email = data.get('email')
            password = data.get('password')
            full_name = data.get('full_name')

            # Check if email already exists in any user type
            if User.query.filter_by(email=email).first() or \
               Doctor.query.filter_by(email=email).first() or \
               Admin.query.filter_by(email=email).first():
                return {'status': 'error', 'message': 'Email already exists'}, 400

            # Create new user (patient by default)
            user = User(
                full_name=full_name,
                email=email,
                role="patient"
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Generate token for immediate login
            access_token = create_access_token(identity=str(user.id))
            
            return {
                'status': 'success',
                'message': 'Registration successful',
                'access_token': access_token,
                'user': user.to_dict()
            }, 201

        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error creating user: {str(e)}')
            return {'status': 'error', 'message': 'Error creating user'}, 500

class DoctorsListResource(Resource):
    def get(self):
        # Support basic filtering
        specialization = request.args.get('specialization')
        city = request.args.get('city')
        
        query = Doctor.query
        
        # Apply filters if provided
        if specialization:
            query = query.filter(Doctor.specialization == specialization)
        if city:
            query = query.filter(Doctor.city == city)
            
        doctors = query.all()
        return {'status': 'success', 'doctors': [doctor.to_dict() for doctor in doctors]}, 200

class DoctorResource(Resource):
    def get(self, doctor_id):
        doctor = Doctor.query.get_or_404(doctor_id)
        return {'status': 'success', 'doctor': doctor.to_dict()}, 200

class AppointmentsListResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            user = Doctor.query.get(user_id)
            
        # Return appointments based on user role
        if user and user.role == 'doctor':
            appointments = Appointment.query.filter_by(doctor_id=user.id).all()
        else:  # Default to patient
            appointments = Appointment.query.filter_by(patient_id=user_id).all()
            
        return {
            'status': 'success', 
            'appointments': [appointment.to_dict() for appointment in appointments]
        }, 200

    @jwt_required()
    def post(self):
        data = request.get_json()
        if not data:
            return {'status': 'error', 'message': 'No data provided'}, 400
        
        # Validate required fields
        required_fields = ['doctor_id', 'appointment_date', 'time_slot', 'illness', 
                         'first_name', 'last_name', 'contact', 'age', 'gender']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return {'status': 'error', 'message': f'Missing required fields: {", ".join(missing_fields)}'}, 400
        
        try:
            # Get patient ID from JWT token
            patient_id = get_jwt_identity()
            
            # Convert date string to date object if needed
            if isinstance(data.get('appointment_date'), str):
                data['appointment_date'] = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
            
            # Create appointment
            appointment = Appointment(
                patient_id=patient_id,
                doctor_id=data['doctor_id'],
                appointment_date=data['appointment_date'],
                time_slot=data['time_slot'],
                illness=data['illness'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                contact=data['contact'],
                age=data['age'],
                gender=data['gender'],
                status='Confirmed'  # Default status
            )
            
            db.session.add(appointment)
            db.session.commit()
            
            return {'status': 'success', 'appointment': appointment.to_dict()}, 201
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error creating appointment: {str(e)}')
            return {'status': 'error', 'message': f'Error creating appointment: {str(e)}'}, 500

class AppointmentResource(Resource):
    @jwt_required()
    def get(self, appointment_id):
        # Get the appointment
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Check if user has permission to view this appointment
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            user = Doctor.query.get(user_id)
            
        # Only patient, doctor, or admin can view the appointment
        if (user and (user.role == 'admin' or 
            (user.role == 'doctor' and user.id == appointment.doctor_id) or 
            (user.id == appointment.patient_id))):
            return {'status': 'success', 'appointment': appointment.to_dict()}, 200
        else:
            return {'status': 'error', 'message': 'Not authorized to view this appointment'}, 403

    @jwt_required()
    def put(self, appointment_id):
        # Get the appointment
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Check permissions
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            user = Doctor.query.get(user_id)
            
        # Only patient, doctor, or admin can update the appointment
        if not (user and (user.role == 'admin' or 
                (user.role == 'doctor' and user.id == appointment.doctor_id) or 
                (user.id == appointment.patient_id))):
            return {'status': 'error', 'message': 'Not authorized to update this appointment'}, 403
            
        # Get and validate data
        data = request.get_json()
        if not data:
            return {'status': 'error', 'message': 'No data provided'}, 400
            
        try:
            # Convert date string to date object if needed
            if 'appointment_date' in data and isinstance(data['appointment_date'], str):
                data['appointment_date'] = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
                
            if 'follow_up_date' in data and data['follow_up_date'] and isinstance(data['follow_up_date'], str):
                data['follow_up_date'] = datetime.strptime(data['follow_up_date'], '%Y-%m-%d').date()
                
            # Update fields
            for key, value in data.items():
                if hasattr(appointment, key):
                    setattr(appointment, key, value)
            
            db.session.commit()
            return {'status': 'success', 'appointment': appointment.to_dict()}, 200
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error updating appointment: {str(e)}')
            return {'status': 'error', 'message': f'Error updating appointment: {str(e)}'}, 500

    @jwt_required()
    def delete(self, appointment_id):
        # Get the appointment
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Check permissions
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            user = Doctor.query.get(user_id)
            
        # Only patient, doctor, or admin can delete the appointment
        if not (user and (user.role == 'admin' or 
                (user.role == 'doctor' and user.id == appointment.doctor_id) or 
                (user.id == appointment.patient_id))):
            return {'status': 'error', 'message': 'Not authorized to delete this appointment'}, 403
            
        try:
            db.session.delete(appointment)
            db.session.commit()
            return {'status': 'success', 'message': 'Appointment deleted successfully'}, 200
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error deleting appointment: {str(e)}')
            return {'status': 'error', 'message': f'Error deleting appointment: {str(e)}'}, 500

class CurrentUserResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        
        # Try to find user in all possible tables
        user = User.query.get(user_id)
        if not user:
            user = Doctor.query.get(user_id)
        if not user:
            user = Admin.query.get(user_id)
            
        if not user:
            return {'status': 'error', 'message': 'User not found'}, 404
            
        return {'status': 'success', 'user': user.to_dict()}, 200

class HealthCheckResource(Resource):
    def get(self):
        try:
            # Check database connection
            db.session.execute('SELECT 1')
            return {
                'status': 'success',
                'message': 'API is healthy',
                'database': 'connected'
            }, 200
        except Exception as e:
            app.logger.error(f'Health check failed: {str(e)}')
            return {
                'status': 'error',
                'message': 'API is unhealthy',
                'database': 'disconnected'
            }, 500

# User loader and decorators
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Access denied! Admin privileges required.", "danger")
            return redirect(url_for('landing'))
        return func(*args, **kwargs)
    return wrapper

def super_admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin:
            flash("Access denied! Super admin privileges required.", "danger")
            return redirect(url_for('landing'))
        return func(*args, **kwargs)
    return wrapper

# Setup logging
def setup_logging(app):
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Healthcare Appointment System startup')

# Error handlers
@jwt.unauthorized_loader
def unauthorized_callback(reason):
    app.logger.warning('Unauthorized access attempt')
    return jsonify({'msg': 'Missing Authorization Header'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(reason):
    app.logger.warning('Invalid token attempt')
    return jsonify({'msg': 'Invalid token'}), 422

@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'Page not found: {request.url}')
    return jsonify({
        'error': 'Resource not found',
        'status': 'error'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Server Error: {error}')
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500

# Create super admin user
def create_super_admin():
    try:
        if not Admin.query.filter_by(is_super_admin=True).first():
            super_admin = Admin(
                full_name='doccure',
                email='admin@doccure.com',
                is_admin=True,
                is_super_admin=True,
                role='super_admin'
            )
            super_admin.set_password('admin123')
            db.session.add(super_admin)
            db.session.commit()
            app.logger.info('Super admin user created successfully')
        else:
            app.logger.info('Super admin user already exists')
    except Exception as e:
        app.logger.error(f'Error creating super admin user: {str(e)}')
        db.session.rollback()

# Routes
@app.route("/")
def landing():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        # First try to find user as a patient
        user = User.query.filter_by(email=email).first()
        
        # If not found as patient, check if they're a doctor
        if not user:
            user = Doctor.query.filter_by(email=email).first()
        
        # If still not found, check if they're an admin
        if not user:
            user = Admin.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("landing"))
        else:
            flash("Invalid credentials!", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if not all([name, email, password, confirm_password]):
            flash("All fields are required!", "danger")
            return redirect(url_for("register"))
        
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("register"))
        
        # Check if email exists in any user type
        if User.query.filter_by(email=email).first() or \
           Doctor.query.filter_by(email=email).first() or \
           Admin.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("register"))
        
        try:
            # Create new user as patient
            new_user = User(
                full_name=name,  # Use the name from the form as full_name
                email=email,
                role="patient"  # Explicitly set role as patient
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error creating user: {str(e)}')
            flash("An error occurred during registration. Please try again.", "danger")
            return redirect(url_for("register"))
            
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for("landing"))

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)

@app.route("/appointments")
@login_required
def appointments():
    if current_user.role == "doctor":
        appointments = Appointment.query.filter_by(doctor_id=current_user.id).all()
    else:
        appointments = Appointment.query.filter_by(patient_id=current_user.id).all()
    return render_template("appointments.html", appointments=appointments)

# Add new route for admin to create doctor accounts
@app.route("/admin/create-doctor", methods=["GET", "POST"])
@login_required
@admin_required
def create_doctor():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        doctor_id = request.form.get("doctor_id")
        specialization = request.form.get("specialization")
        experience = request.form.get("experience")
        city = request.form.get("city")
        fees = request.form.get("fees")
        
        # Check if email exists in any user type
        if User.query.filter_by(email=email).first() or \
           Doctor.query.filter_by(email=email).first() or \
           Admin.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("create_doctor"))
        
        # Check if doctor_id already exists
        if Doctor.query.filter_by(user_id=doctor_id).first():
            flash("Doctor ID already exists!", "danger")
            return redirect(url_for("create_doctor"))
        
        # Create new doctor
        new_doctor = Doctor(
            full_name=name,
            email=email,
            user_id=doctor_id,
            specialization=specialization,
            experience=experience,
            city=city,
            fees=fees,
            role="doctor"
        )
        new_doctor.set_password(password)
        db.session.add(new_doctor)
        db.session.commit()
        flash("Doctor account created successfully!", "success")
        return redirect(url_for("admin_dashboard"))
    
    return render_template("admin/create_doctor.html")

# Add admin dashboard route
@app.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    doctors = Doctor.query.all()
    patients = User.query.filter_by(role="patient").all()
    return render_template("admin/dashboard.html", doctors=doctors, patients=patients)

# Add super admin dashboard route
@app.route("/super-admin/dashboard")
@login_required
@super_admin_required
def super_admin_dashboard():
    admins = Admin.query.all()
    doctors = Doctor.query.all()
    patients = User.query.filter_by(role="patient").all()
    return render_template("admin/super_dashboard.html", 
                         admins=admins, 
                         doctors=doctors, 
                         patients=patients)

# Add admin appointment management routes
@app.route("/admin/appointments")
@login_required
@admin_required
def admin_appointments():
    appointments = Appointment.query.all()
    return render_template("admin/appointments.html", appointments=appointments)

@app.route("/admin/appointments/<int:appointment_id>/update", methods=["POST"])
@login_required
@admin_required
def update_appointment_status(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    new_status = request.form.get("status")
    if new_status in ["Confirmed", "Cancelled", "Completed"]:
        appointment.status = new_status
        db.session.commit()
        flash(f"Appointment status updated to {new_status}", "success")
    else:
        flash("Invalid status", "danger")
    return redirect(url_for("admin_appointments"))

@app.route("/admin/appointments/<int:appointment_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    db.session.delete(appointment)
    db.session.commit()
    flash("Appointment deleted successfully", "success")
    return redirect(url_for("admin_appointments"))

# Add admin statistics route
@app.route("/admin/statistics")
@login_required
@admin_required
def admin_statistics():
    total_doctors = Doctor.query.count()
    total_patients = User.query.filter_by(role="patient").count()
    total_appointments = Appointment.query.count()
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(5).all()
    
    # Get appointments by status
    confirmed_appointments = Appointment.query.filter_by(status="Confirmed").count()
    cancelled_appointments = Appointment.query.filter_by(status="Cancelled").count()
    completed_appointments = Appointment.query.filter_by(status="Completed").count()
    
    return render_template("admin/statistics.html",
                         total_doctors=total_doctors,
                         total_patients=total_patients,
                         total_appointments=total_appointments,
                         recent_appointments=recent_appointments,
                         confirmed_appointments=confirmed_appointments,
                         cancelled_appointments=cancelled_appointments,
                         completed_appointments=completed_appointments)

# Add admin doctor management routes
@app.route("/admin/doctors")
@login_required
@admin_required
def admin_doctors():
    doctors = Doctor.query.all()
    return render_template("admin/doctors.html", doctors=doctors)

@app.route("/admin/doctors/<int:doctor_id>/update", methods=["POST"])
@login_required
@admin_required
def update_doctor_status(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_available = not doctor.is_available
    db.session.commit()
    status = "available" if doctor.is_available else "unavailable"
    flash(f"Doctor is now {status}", "success")
    return redirect(url_for("admin_doctors"))

# Add admin patient management routes
@app.route("/admin/patients")
@login_required
@admin_required
def admin_patients():
    patients = User.query.filter_by(role="patient").all()
    return render_template("admin/patients.html", patients=patients)

@app.route("/admin/patients/<int:patient_id>/appointments")
@login_required
@admin_required
def patient_appointments(patient_id):
    patient = User.query.get_or_404(patient_id)
    appointments = Appointment.query.filter_by(patient_id=patient_id).all()
    return render_template("admin/patient_appointments.html", 
                         patient=patient, 
                         appointments=appointments)

@app.route('/api/doctors/<int:doctor_id>/slots', methods=['GET'])
def get_doctor_available_slots(doctor_id):
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'status': 'error', 'message': 'Date parameter is required'}), 400
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format, should be YYYY-MM-DD'}), 400

    # Define working hours (9:00 to 18:00)
    start_hour = 9
    end_hour = 18
    all_slots = [f"{hour:02d}:00 - {hour+1:02d}:00" for hour in range(start_hour, end_hour)]

    # Get booked slots for the doctor on the given date
    booked_appointments = Appointment.query.filter_by(doctor_id=doctor_id, appointment_date=date_obj).all()
    booked_slots = set([appt.time_slot for appt in booked_appointments])

    # Exclude booked slots
    available_slots = [slot for slot in all_slots if slot not in booked_slots]

    return jsonify({'status': 'success', 'slots': available_slots}), 200

# API Routes
api.add_resource(LoginResource, '/api/login/')
api.add_resource(RegisterResource, '/api/register/')
api.add_resource(DoctorsListResource, '/api/doctors/')
api.add_resource(DoctorResource, '/api/doctors/<int:doctor_id>/')
api.add_resource(AppointmentsListResource, '/api/appointments/')
api.add_resource(AppointmentResource, '/api/appointments/<int:appointment_id>/')
api.add_resource(CurrentUserResource, '/api/me/')
api.add_resource(HealthCheckResource, '/api/health/')

# Initialize application
if __name__ == '__main__':
    # Setup logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create database tables and super admin user if they don't exist
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Create super admin if none exists
        if not Admin.query.filter_by(is_super_admin=True).first():
            create_super_admin()
            app.logger.info('Super admin user created')
        else:
            app.logger.info('Super admin user already exists')
    
    # Run the application
    app.run(
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )