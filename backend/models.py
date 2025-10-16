from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bcrypt import Bcrypt

# Initializing the database and bcrypt
db = SQLAlchemy()
bcrypt = Bcrypt()

class Members(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)
    role = db.Column(db.String(20))
    address = db.Column(db.String(280), nullable=False)
    pincode= db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    last_logged_in = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), nullable=False, default="active")

    # Relationship
    
    booking = db.relationship('Booking', back_populates='user', lazy=True, cascade="all, delete-orphan")
    rating = db.relationship('Rating', back_populates='user', lazy=True, cascade="all, delete-orphan")
    
    def __init__(self, name, email, role, address, password, pincode):
        self.name = name
        self.email = email
        self.role = role
        self.address = address
        self.pincode = pincode
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

class Servicetypes(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    servicetype = db.Column(db.String(80), nullable=False)
    baseprice = db.Column(db.Integer, nullable=False)
    servicetype_photo_filename= db.Column(db.String(128), nullable=False)
    # Relationship
    profressinal = db.relationship('Profressinal', back_populates='servicetype', lazy=True, cascade="all, delete-orphan")
    booking = db.relationship('Booking', back_populates='servicetype', lazy=True, cascade="all, delete-orphan")
    def __init__(self, servicetype,servicetype_photo_filename, baseprice):
        self.servicetype = servicetype
        self.servicetype_photo_filename=servicetype_photo_filename
        self.baseprice = baseprice


class Profressinal(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    profressionaltype = db.Column(db.String(80), nullable=False)
    servicetype_id = db.Column(db.Integer, db.ForeignKey('servicetypes.id'), nullable=False)
    servicename = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(280), nullable=False)
    address = db.Column(db.String(280), nullable=False)
    pincode= db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(80), nullable=False)
    contact = db.Column(db.String(80), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(80), nullable=False)
    timerequired = db.Column(db.Integer, nullable=False)
    bookingcharge = db.Column(db.Integer, nullable=False)
    tags = db.Column(db.String(280), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    datecreated = db.Column(db.DateTime, default=datetime.now)    
    servicephoto_filename = db.Column(db.String(128), nullable=False)
    lisence_filename = db.Column(db.String(128), nullable=False)
    approvalstatus = db.Column(db.String(20), nullable=False, default="pending")
    status = db.Column(db.String(20), nullable=False, default="active")
    averagerating = db.Column(db.Float, nullable=False, default=0.0) 
    # Relationship
    servicetype = db.relationship('Servicetypes', back_populates='profressinal', lazy=True)
    booking = db.relationship('Booking', back_populates='professional', lazy=True, cascade="all, delete-orphan")
    rating = db.relationship('Rating', back_populates='professional', lazy=True, cascade="all, delete-orphan")
    
    def __init__(self, name, servicename, servicetype_id, profressionaltype, description, address,pincode, email, contact, experience, role, password, servicephoto_filename, lisence_filename, timerequired, bookingcharge, tags):
        self.name = name
        self.profressionaltype = profressionaltype
        self.servicetype_id = servicetype_id
        self.servicename = servicename
        self.description = description
        self.address = address
        self.pincode = pincode
        self.email = email
        self.contact = contact
        self.experience = experience
        self.role = role
        self.timerequired = timerequired
        self.bookingcharge = bookingcharge
        self.tags = tags
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.servicephoto_filename = servicephoto_filename
        self.lisence_filename = lisence_filename


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('profressinal.id'), nullable=False)
    servicetype_id = db.Column(db.Integer, db.ForeignKey('servicetypes.id'), nullable=False)
    booking_date = db.Column(db.Date,  default=datetime.now)
    service_date = db.Column(db.Date, nullable=False)
    service_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default="pending")
    booking_charge = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(280), nullable=False)
    notes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.now)
    # Relationship
    user = db.relationship('Members', back_populates='booking', lazy=True)
    professional = db.relationship('Profressinal', back_populates='booking', lazy=True)
    servicetype = db.relationship('Servicetypes', back_populates='booking', lazy=True)
    rating = db.relationship('Rating', back_populates='booking', lazy=True)

    def __init__(self, user_id, professional_id, servicetype_id, service_date, service_time, booking_charge, address, notes, booking_date=None, status="pending"):
        self.user_id = user_id
        self.professional_id = professional_id
        self.servicetype_id = servicetype_id
        self.booking_date = booking_date if booking_date else datetime.now()
        self.service_date = service_date
        self.service_time = service_time
        self.status = status
        self.booking_charge = booking_charge
        self.address = address
        self.notes = notes

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('profressinal.id'), nullable=False)
    Booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text)
    # Relationship
    user = db.relationship('Members', back_populates='rating', lazy=True)
    professional = db.relationship('Profressinal', back_populates='rating', lazy=True)
    booking = db.relationship('Booking', back_populates='rating', lazy=True)

    def __init__(self, user_id, professional_id, Booking_id, rating, review):
        self.user_id = user_id
        self.professional_id = professional_id
        self.Booking_id = Booking_id
        self.rating = rating
        self.review = review
        