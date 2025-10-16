from flask import Flask, jsonify, request, send_from_directory, send_file, Response
from config import Config
from models import *
from flask_cors import CORS
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager, unset_jwt_cookies
from werkzeug.utils import secure_filename
import os
import json
import pandas as pd
import requests
from tools import workers, tasks, mailer
from flask_caching import Cache
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
import io
import csv



app = Flask(__name__)
app.config.from_object(Config)


db.init_app(app)
bcrypt.init_app(app)
jwt=JWTManager(app)
mailer.init_app(app)
cache = Cache(app)


celery = workers.celery
celery.conf.update(
    broker_url=app.config['CELERY_BROKER_URL'],
    result_backend=app.config['CELERY_RESULT_BACKEND']
)

celery.Task= workers.ContextTask

app.app_context().push() 

app_name="ServiceSync"

def admincheck(): 

    admincheking = Members.query.filter_by(role="admin").first()
    if admincheking:
        return jsonify({"message":"Admin exsits."}),200
    else:
        try:
        
            admin = Members(
                name='admin',
                email='admin@servicesync.com',
                role='admin',
                address="ServiceSync Headquarters",
                pincode=123456,
                password=('123')
                
            )
            db.session.add(admin)
            db.session.commit() 

            print("Admin created")
            
            servicetype_list=['Appliance Services', 'Plumbing Services',
                                'Electrical Services', 'Painting Services',
                                'Carpentry Services', 'Cleaning Services',
                                'Gardening Services', 'House Security Services',
                                'Pest Control Services','Home Renovation and Construction Services',
                                'Laundry Services','Others and Miscellaneous' ]
            
            for servicetype in servicetype_list:
                photo_filename = f"{servicetype.replace(' ', '_')}.png"
                service = Servicetypes(servicetype=servicetype, servicetype_photo_filename=photo_filename,baseprice=100)
                db.session.add(service)
                db.session.commit()
            

            return jsonify({"message": "New admin and Service Types were created. Thank You."}), 200

        except Exception as e:
            db.session.rollback()  
            print(f"Error occurred: {str(e)}")  
            return jsonify({"error": str(e)}), 500



with app.app_context():
    db.create_all()
    admincheck()

CORS(app, supports_credentials=True)


@app.route("/")
def home():
    #mailer.send_email("4c4w2@example.com", "Welcome to ServiceSync", "Welcome to ServiceSync")
    # tasks.send_daily_reminder.delay()
    # tasks.send_pending_service_reminder.delay()
    return( app_name)

@app.route("/registration/user", methods=['POST'])
def registeruser():
    data = request.json

    name=data.get('name')
    email=data.get('email')
    role="customer"
    address=data.get('address')
    pincode=data.get('pincode')
    password=data.get('password')

    if not name or not email or not address or not password or not pincode:
        return jsonify({'error':'Required Field/Fields is/are missing'}),400
    
    already_reg = Members.query.filter_by(email=email).first()

    if already_reg:
        return jsonify({"error":'email already been used.'}),400


    try:
        customer = Members(name=name, email=email, role=role, address=address, pincode=pincode, password=password)

        db.session.add(customer)
        db.session.commit()
        return jsonify({'message':'User created Sucessfully'}),200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/registration/professional", methods=['POST'])
def registerprofessional():
    

    name=request.form.get('name')
    professionaltype=request.form.get('professionaltype')
    servicetype=request.form.get('servicetype')
    servicename=request.form.get('servicename')
    description=request.form.get('description')
    address=request.form.get('address')
    pincode=request.form.get('pincode')
    email=request.form.get('email')
    contact=request.form.get('contact')
    experience=request.form.get('experience')
    role="professional"
    timerequired=request.form.get('timerequired')
    bookingcharge=request.form.get('bookingcharge')
    tags=request.form.get('tags')
    password=request.form.get('password')
    photo=request.files.get('photo')
    lisence=request.files.get('lisence')

    if not name or not professionaltype or not servicetype or not servicename or not description or not address or not email or not contact or not experience or not password or not photo or not lisence or not timerequired or not pincode or not bookingcharge or not tags:
        return jsonify({'error':'Required Field/Fields is/are missing'}),400

    already_reg = Profressinal.query.filter_by(email=email).first()

    if already_reg:
        return jsonify({"error":'email already been used.'}),400
    already_reg_serv = Profressinal.query.filter_by(servicename=servicename).first()

    if already_reg_serv:
        return jsonify({"error":'Service name already been used.'}),400
    
    service_category = Servicetypes.query.filter_by(servicetype=servicetype).first()

    if not service_category:
        return jsonify({"error":'Service type does not exist.'}),400
    else:
        servicetype_id=service_category.id

    photo_filename= secure_filename(servicename+".png")
    photo_path=(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
    os.makedirs(os.path.dirname(photo_path), exist_ok=True)
    photo.save(photo_path)

    lisence_filename= secure_filename(servicename+".pdf")
    lisence_path=(os.path.join(app.config['UPLOAD_FOLDER'], lisence_filename))
    os.makedirs(os.path.dirname(lisence_path), exist_ok=True)
    lisence.save(lisence_path)

    try:
        servicereg=Profressinal(name=name,servicename=servicename,servicetype_id=servicetype_id,profressionaltype=professionaltype,description=description,address=address, pincode=pincode,email=email,contact=contact,experience=experience,role=role,password=password,servicephoto_filename=photo_filename,lisence_filename=lisence_filename,timerequired=timerequired,bookingcharge=bookingcharge,tags=tags)
        db.session.add(servicereg)
        db.session.commit()
        return jsonify({'message':'Service Professional profile created Sucessfully'}),200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@app.route("/login/user", methods=['POST'])
def loginuser():
    data = request.json

    email=data.get('email')
    password=data.get('password')

    if not email or not password:
        return jsonify({'error':'Required Field/Fields is/are missing'}),400

    customer = Members.query.filter_by(email=email).first()

    if customer:
        curr_pass = bcrypt.check_password_hash(customer.password, password)
        if curr_pass:
            if customer.status == 'blocked':
                return jsonify({'error': 'Your account has been blocked.'}), 401
            else:

                access_token = create_access_token(identity={'id': customer.id, 'email': customer.email,'role':customer.role})
                customer.last_logged_in = datetime.now()
                db.session.commit()
                return jsonify({"message": "Login successful", 'access_token': access_token, 'role':customer.role}), 200
                
        else:
            return jsonify({'error': 'Invalid password'}), 401
    else:
        return jsonify({'error': 'Invalid email'}), 401
    

@app.route("/login/professional", methods=['POST'])
def loginprofessional():
    data = request.json

    email=data.get('email')
    password=data.get('password')

    if not email or not password:
        return jsonify({'error':'Required Field/Fields is/are missing'}),400

    profressinal = Profressinal.query.filter_by(email=email).first()

    if profressinal:
        curr_pass = bcrypt.check_password_hash(profressinal.password, password)
        if curr_pass:
            if profressinal.status == 'block':
                return jsonify({'error': 'Your account has been blocked.'}), 401
            elif profressinal.approvalstatus == 'rejected':
                return jsonify({'error': 'Your account has been rejected by admin. Please contact admin.'}), 401
            else:
                access_tokenpr = create_access_token(identity={'id': profressinal.id, 'email': profressinal.email,'role':profressinal.role})
                return jsonify({"message": "Login successful for Professional", 'access_token': access_tokenpr}), 200

        else:
            return jsonify({'error': 'Invalid password'}), 401
    else:
        return jsonify({'error': 'Invalid email'}), 401


@app.route("/get/details/user",methods=['GET'])
@jwt_required()
def getuserdetails():
    current_user = get_jwt_identity()
    email= current_user['email']
    user=Members.query.filter_by(email=email).first()
    print(user)
    return jsonify({'name':user.name,'email':user.email,'role':user.role,'address':user.address,'pincode':user.pincode,'id':user.id}),200

@app.route("/get/details/professional",methods=['GET'])
@jwt_required()
def getprofessionaldetails():
    current_user = get_jwt_identity()
    email= current_user['email']
    profressinal=Profressinal.query.filter_by(email = email).first()
    print(profressinal)
    return jsonify({'name':profressinal.name,'email':profressinal.email,'role':profressinal.role,"servicename":profressinal.servicename,'address':profressinal.address,'pincode':profressinal.pincode,'contact':profressinal.contact,'description':profressinal.description,'experience':profressinal.experience,'timerequired':profressinal.timerequired,'servicephoto':profressinal.servicephoto_filename,'lisence':profressinal.lisence_filename}),200

@app.route("/get/servicetypes",methods=['GET'])
def getservicetypes():
    servicetypes=Servicetypes.query.all()
    s_types=[]
    for servicetype in servicetypes:    
        s_types.append({'id':servicetype.id,'servicetype':servicetype.servicetype,'photo':servicetype.servicetype_photo_filename,'baseprice':servicetype.baseprice})
    return jsonify({'servicetypes':s_types}),200

@app.route("/get/service/type/<int:id>",methods=['GET'])
@cache.cached(timeout=30)
def getservicetype(id):
    servicetype=Servicetypes.query.filter_by(id=id).first()
    return jsonify({'servicetype':servicetype.servicetype, 'baseprice':servicetype.baseprice}),200

@app.route("/update/user",methods=['PUT'])
@jwt_required()
def updateuser():
    current_user = get_jwt_identity()
    email= current_user['email']
    user=Members.query.filter_by(email=email).first()
    data=request.json
    name=data.get('name')
    address=data.get('address')
    pincode=data.get('pincode')

    if not name or not address or not pincode:
        return jsonify({'error':'Required Field/Fields is/are missing'}),400

    user.name=name
    user.address=address
    user.pincode=pincode
    db.session.commit()
    
    
    return jsonify({'message':'User details updated successfully'}),200


@app.route("/uploads/<filename>",methods=['GET'])
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



@app.route("/update/professional",methods=['PUT'])
@jwt_required()
def updatprofessional():
    current_user = get_jwt_identity()
    email= current_user['email']
    profressinal=Profressinal.query.filter_by(email=email).first()
    data=request.json
    name=data.get('name')
    servicename=data.get('servicename')
    description=data.get('description')
    address=data.get('address')
    pincode=data.get('pincode')
    contact=data.get('contact')
    experience=data.get('experience')
    timerequired=data.get('timerequired')
   
    
    if not name or not servicename or not description or not address or not contact or not experience or not timerequired or not pincode:
        return jsonify({'error':'Required Field/Fields is/are missing'}),400
    

    #as we also have service name as an unique constraint:
    already_reg_serv = Profressinal.query.filter(
        Profressinal.servicename == servicename,
        Profressinal.id != profressinal.id  # Ignore the original professional's record
    ).first()

    if already_reg_serv:
        return jsonify({'error': 'Service name already been used by another professional'}), 400
    
    profressinal.name=name
    profressinal.servicename=servicename
    profressinal.description=description   
    profressinal.address=address
    profressinal.pincode=pincode
    profressinal.contact=contact
    profressinal.experience=experience
    profressinal.timerequired=timerequired
    db.session.commit()
    
    
    return jsonify({'message':'Professional details updated successfully'}),200

@app.route("/get/all/professionals",methods=['GET'])
# @cache.cached(timeout=60) No point as it will lead to refresshing the page to get up to date data

def getallprofessionals():

    professionals=Profressinal.query.all()
    profs_data=[]
    for professional in professionals:
        dates=professional.datecreated.strftime('%d-%b-%Y')
        date={'date':dates}
        profs_data.append({
            'id':professional.id,
            'date':date,
            'servicename':professional.servicename,
            'lisence':professional.lisence_filename,
            'status':professional.status,
            'approval':professional.approvalstatus,
            'description':professional.description,
            'pincode':professional.pincode,
            'name':professional.name,
            'address':professional.address,
            'bookingcharge':professional.bookingcharge,
            'tags':professional.tags,
            

            })
        
    return jsonify({'professionals':profs_data}),200
@app.route("/get/all/customers",methods=['GET'])
def getallcustomers():
    customers = Members.query.filter(Members.id != 1).all()
    customers_data=[]
    for customer in customers:
        last_logg = customer.last_logged_in.strftime('%d-%b-%Y, %I:%M %p')
        date = {'datec':last_logg}
        customers_data.append({
            'id':customer.id,
            'name':customer.name,
            'email':customer.email,
            'pincode':customer.pincode,
            'last_logged_in':date,
            'status':customer.status
            })
    return jsonify({"customers":customers_data}),200

@app.route("/get/professional/<int:id>",methods=['GET'])
def getprofessional(id):
    professional=Profressinal.query.filter_by(id=id).first()
    professional_data={
            'id':professional.id,
            'date':professional.datecreated,
            'servicename':professional.servicename,
            'lisence':professional.lisence_filename,
            'stsatus':professional.status,
            'name':professional.name,
            'email':professional.email,
            'contact':professional.contact,
            'address':professional.address,
            'pincode':professional.pincode,
            'description':professional.description,
            'experience':professional.experience,
            'timerequired':professional.timerequired,
            'servicephoto':professional.servicephoto_filename,}
    return jsonify({'professional':professional_data}),200

@app.route("/review/professional/<int:id>",methods=['PUT'])
@jwt_required()
def reviewprofessional(id):
    current_user = get_jwt_identity()
    role=current_user['role']
    if role=='admin':
        data=request.json
        status=data.get('status')
        approvalstatus=data.get('approvalstatus')
        professional=Profressinal.query.filter_by(id=id).first()
        if status:
            approvalstatus=professional.approvalstatus
        elif approvalstatus:
            status=professional.status
        else:
            return jsonify({'message':'Status or approval status is missing'}),400
            
        professional.status=status
        professional.approvalstatus=approvalstatus
        db.session.commit()
        return jsonify({'message':'Professional details updated successfully'}),200
    else:
        return jsonify({'message':'You are not an admin'}),401
    
@app.route("/block/professional/<int:id>",methods=['PUT'])
@jwt_required()
def blockprofessional(id):
    current_user = get_jwt_identity()
    role=current_user['role']
    if role=='admin':
        professional=Profressinal.query.filter_by(id=id).first()
        professional.status='blocked'
        db.session.commit()
        return jsonify({'message':'Professional blocked successfully'}),200
    else:
        return jsonify({'message':'You are not an admin'}),401
@app.route("/blockunblock/customer/<int:id>",methods=['PUT'])
@jwt_required()
def blockunblockcustomer(id):
    current_user = get_jwt_identity()
    role=current_user['role']
    if role=='admin':
        customer=Members.query.filter_by(id=id).first()
        if customer.status=='active':
            customer.status='blocked'
            db.session.commit()
            return jsonify({'message':'Customer blocked successfully'}),200
        else:
            customer.status='active'
            db.session.commit()
            return jsonify({'message':'Customer unblocked successfully'}),200
    else:
        return jsonify({'message':'You are not an admin'}),401
 


@app.route("/get/public/profile/professional/<int:id>",methods=['GET'])
@cache.cached(timeout=30)
def getpublicprofessional(id):
    professional=Profressinal.query.filter_by(id=id).first()
    professional_data={
            'id':professional.id,
            'date':professional.datecreated,
            'servicename':professional.servicename,
            'professionaltype':professional.profressionaltype,
            'servicetype':professional.servicetype.servicetype,
            'servicetypeid':professional.servicetype.id,
            'name':professional.name,
            'email':professional.email,
            'contact':professional.contact,
            'address':professional.address,
            'pincode':professional.pincode,
            'description':professional.description,
            'experience':professional.experience,
            'timerequired':professional.timerequired,
            'bookingcharge':professional.bookingcharge,
            'tags':professional.tags,
            'servicephoto':professional.servicephoto_filename,
            'rating':professional.averagerating,}
    return jsonify({'professional':professional_data}),200

@app.route("/add/service/type",methods=['POST'])
@jwt_required()
def addservicetype():
    current_user = get_jwt_identity()
    role=current_user['role']
    if role=='admin':
        servicetype=request.form.get('servicetype')
        baseprice=request.form.get('baseprice')
        photo=request.files.get('photo')

        if not servicetype or not photo or not baseprice:
            return jsonify({'error':'Required Field/Fields is/are missing'}),400

        already_reg = Servicetypes.query.filter_by(servicetype=servicetype).first()  

        if already_reg:
            return jsonify({'error':'Service type already registered'}),400 
        
        photo_filename= secure_filename(servicetype+".png")
        photo_path=(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        os.makedirs(os.path.dirname(photo_path), exist_ok=True)
        photo.save(photo_path)

        new_service_type=Servicetypes(servicetype=servicetype,baseprice=baseprice,servicetype_photo_filename=photo_filename)
        db.session.add(new_service_type)
        db.session.commit()
        return jsonify({'message':'Service type added successfully'}),200

@app.route("/delete/service/type/<int:id>",methods=['DELETE'])
@jwt_required()
def deleteservicetype(id):
    current_user = get_jwt_identity()
    role=current_user['role']
    if role=='admin':
        servicetype=Servicetypes.query.filter_by(id=id).first()
        db.session.delete(servicetype)
        db.session.commit()
        return jsonify({'message':'Service type deleted successfully'}),200
    else:
        return jsonify({'message':'You are not an admin'}),401
    
@app.route("/update/service/type/<int:id>", methods=['PUT'])
@jwt_required()
def updateservicetype(id):
    current_user = get_jwt_identity()
    role = current_user['role']

    if role == 'admin':
        data = request.json
        new_service_type = data.get('servicetype')  # Get the new service type from request body
        baseprice = data.get('baseprice')  # Get the new base price from request body
        if not new_service_type or not baseprice:
            return jsonify({'message': 'Service type and base price is required'}), 400  # Validation error



        # Find the service type by ID
        servicetype = Servicetypes.query.filter_by(id=id).first()
        if not servicetype:
            return jsonify({'message': 'Service type not found'}), 404  # ID not found
        
        alredy_service = Servicetypes.query.filter(Servicetypes.servicetype == new_service_type, Servicetypes.id != id).first()
        
        if alredy_service:
            return jsonify({'message': 'Service type already exists'}), 409

        servicetype.servicetype = new_service_type  # Update the service type
        servicetype.baseprice = baseprice  # Update the base price
        db.session.commit()  # Save changes to the database

        return jsonify({'message': 'Service type updated successfully'}), 200
    else:
        return jsonify({'message': 'You are not an admin'}), 401
    
@app.route("/get/service/type/professionals/<int:id>",methods=['GET'])
@cache.cached(timeout=30)
def getservicetypeprofessionals(id):
    professionals = Profressinal.query.filter_by(servicetype_id=id).order_by(Profressinal.averagerating.desc()).all()
    professionals_data = []
    for professional in professionals:
        if professional.approvalstatus=='approved':
            professionals_data.append({
                'id':professional.id,
                'servicename':professional.servicename,
                'pincode':professional.pincode,
                'bookingcharge':professional.bookingcharge,
                'photo':professional.servicephoto_filename,
                'type':professional.servicetype.servicetype,
                'rating':professional.averagerating,
                'address':professional.address,
                'tags':professional.tags
            })
    return jsonify({'professionals':professionals_data}),200
# @app.route("/get/date/time",methods=['GET'])
# def getdatetime(datetimeobj):
#     date=datetimeobj.date()
#     time=datetimeobj.time()
#     return jsonify({'date':date,'time':time}),200

@app.route("/protected/about",methods=['GET'])
@jwt_required()
def protectedabout():
    current_user = get_jwt_identity()
    if current_user['role']=='admin':
        return jsonify({'message':'You are an admin'}),200
    else:
        return jsonify({'message':'You are not an admin'}),401


@app.route("/book/service", methods=["POST"])
@jwt_required()
def book_service():
    data = request.json
    user_id = get_jwt_identity()["id"]
    professional_id = data.get("professional_id")
    servicetype_id = data.get("servicetype_id") 
    service_date = data.get("service_date")
    service_time = data.get("service_time")
    notes = data.get("notes", "")
    print(f"Received data: {data}")
    
    if not professional_id or not servicetype_id or not service_date or not service_time:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        # Convert `service_date` and `service_time` to proper types
        service_date = datetime.strptime(service_date, "%Y-%m-%d").date()  # Convert to `datetime.date`
        service_time = datetime.strptime(service_time, "%H:%M").time()     # Convert to `datetime.time`
    except ValueError as e:
        return jsonify({"error": f"Invalid date or time format: {str(e)}"}), 400

 
    professional = Profressinal.query.filter_by(id=professional_id).first()
    if not professional:
        return jsonify({"error": "Professional not found"}), 404
    booking_charge = professional.bookingcharge

    member = Members.query.filter_by(id=user_id).first()
    if not member:
        return jsonify({"error": "User not found"}), 404
    address = member.address

    # Create and save the new booking
    new_booking = Booking(
        user_id=user_id,
        professional_id=professional_id,
        servicetype_id=servicetype_id,
        service_date=service_date,
        service_time=service_time,
        address=address,
        notes=notes,
        booking_charge=booking_charge
    )

    db.session.add(new_booking)
    db.session.commit()

    return jsonify({"message": "Service booked successfully"}), 200   


@app.route("/get/bookings/<status>", methods=["GET"])
@jwt_required()
def getbookings(status):
    if get_jwt_identity()["role"] == "customer" or get_jwt_identity()["role"] == "admin":
        user_id = get_jwt_identity()["id"]
        bookings = Booking.query.filter_by(user_id=user_id, status=status).all()
        
        bookings_data = []
        for booking in bookings:
            service_time = booking.service_time.strftime('%H:%M:%S')
            service_date = booking.service_date.strftime('%Y-%m-%d')
            updated_date=booking.updated_at.strftime('%Y-%m-%d')
            bookings_data.append({
                'id':booking.id,
                'userid':booking.user_id,
                'professionalid':booking.professional_id,
                'servicetypeid':booking.servicetype_id,
                'servicename':booking.professional.servicename,
                'servicetype':booking.servicetype.servicetype,
                'servicedate':service_date,
                'servicetime':service_time,
                'address':booking.address,
                'notes':booking.notes,
                'bookingcharge':booking.booking_charge,
                'status':booking.status,
                'completiondate':updated_date
            })

            
        return jsonify({'bookings':bookings_data}),200
    elif get_jwt_identity()["role"] == "professional":
        professional_id = get_jwt_identity()["id"]
        bookings = Booking.query.filter_by(professional_id=professional_id, status=status).all()
        bookings_data = []
        for booking in bookings:
            service_time = booking.service_time.strftime('%H:%M:%S')
            service_date = booking.service_date.strftime('%Y-%m-%d')
            booking_date=booking.service_date.strftime('%Y-%m-%d')
            updated_date=booking.updated_at.strftime('%Y-%m-%d')
            bookings_data.append({
                'id':booking.id,
                'userid':booking.user_id,
                'professionalid':booking.professional_id,
                'servicetypeid':booking.servicetype_id,
                'customername':booking.user.name,
                'servicedate':service_date,
                'servicetime':service_time,
                'address':booking.address,
                'notes':booking.notes,
                'bookingdate':booking_date,
                'status':booking.status,
                'completiondate':updated_date
            })
        return jsonify({'bookings':bookings_data}),200

@app.route("/get/booking/<int:booking_id>", methods=["GET"])
@jwt_required()
def getbooking(booking_id):
    if get_jwt_identity()["role"] == "customer":
        booking = Booking.query.filter_by(id=booking_id).first()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        booking_data = {
            'id':booking.id,
            'userid':booking.user_id,
            'professionalid':booking.professional_id,
            'servicetypeid':booking.servicetype_id,
            'servicename':booking.professional.servicename,
            'servicephoto':booking.professional.servicephoto_filename,
            'professionalemail':booking.professional.email,
            'professionalcontact':booking.professional.contact,
            'professionaltype':booking.professional.profressionaltype,
            'professionalname':booking.professional.name,
            'servicetype':booking.servicetype.servicetype,
            'address':booking.address,
            'bookingcharge':booking.booking_charge,
            'servicedate':booking.service_date.strftime('%Y-%m-%d'),
            'servicetime':booking.service_time.strftime('%H:%M:%S'),
            'notes':booking.notes,
            
            
        }
        return jsonify({'booking':booking_data}),200
    else:
        return jsonify({"error": "Unauthorized"}), 401
@app.route("/approve/booking/<int:booking_id>", methods=["PUT"])
@jwt_required()
def approvebooking(booking_id):
    if get_jwt_identity()["role"] == "professional":
        booking = Booking.query.filter_by(id=booking_id).first()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        booking.status = "approved"
        db.session.commit()
        return jsonify({"message": "Booking approved successfully"}), 200
    elif get_jwt_identity()["role"] == "customer":
        booking = Booking.query.filter_by(id=booking_id).first()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        booking.status = "completed"
        booking.updated_at = datetime.now()
        db.session.commit()
        return jsonify({"message": "Booking completed successfully"}), 200  
@app.route("/reject/booking/<int:booking_id>", methods=["PUT"])
@jwt_required()
def rejectbooking(booking_id):
    if get_jwt_identity()["role"] == "professional":
        booking = Booking.query.filter_by(id=booking_id).first()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        booking.status = "rejected"
        booking.updated_at = datetime.now()
        db.session.commit()
        return jsonify({"message": "Booking rejected successfully"}), 200

@app.route("/rate/booking/<int:booking_id>", methods=["POST"])
@jwt_required()
def ratebooking(booking_id):
    if get_jwt_identity()["role"] == "customer":
        booking = Booking.query.filter_by(id=booking_id).first()
        booking.status = "completed"
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        user_id = get_jwt_identity()["id"]
        professional_id = Profressinal.query.filter_by(id=booking.professional_id).first().id
        rating = request.json.get("rating")
        review = request.json.get("review")
        if not rating or not review:
            return jsonify({"error": "Rating and review are required"}), 400
        rating = Rating(user_id=user_id, Booking_id=booking_id, rating=rating, review=review, professional_id=professional_id)
        db.session.add(rating)
        db.session.commit()
        pid = booking.professional_id
        rates = Rating.query.filter_by(professional_id=pid).all()
        average_rating =  round(sum(rate.rating for rate in rates) / len(rates))
        professional = Profressinal.query.filter_by(id=professional_id).first()
        professional.averagerating = average_rating
        db.session.commit()
        return jsonify({"message": "Rating submitted and service closed successfully"}), 200

@app.route("/update/booking/<int:booking_id>", methods=["PUT"])
@jwt_required()
def updatebooking(booking_id):
    if get_jwt_identity()["role"] == "customer":
        booking = Booking.query.filter_by(id=booking_id).first()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if booking.status == "pending":
            data = request.json
            servicedate = data.get("servicedate")
            servicetime = data.get("servicetime")
            address = data.get("address")
            notes = data.get("notes")
            
            # Validate required fields
            if not servicedate or not servicetime or not address:
                print('data',data)
                return jsonify({"error": "Missing required fields (service date, time, or address)."}), 400
            
            # Parse date and time
            try:
                booking.service_date = datetime.strptime(servicedate, "%Y-%m-%d").date()
                booking.service_time = datetime.strptime(servicetime, "%H:%M:%S").time()
            except ValueError:
                booking.service_time = datetime.strptime(servicetime, "%H:%M").time()
            
            # Update fields
            booking.address = address
            booking.notes = notes or "" 
            db.session.commit()
            return jsonify({"message": "Booking updated successfully"}), 200
        else:
            return jsonify({"error": "Booking has already progressed to the next stage...!"}), 400



@app.route("/get/reviews", methods=["GET"])
@cache.cached(timeout=30)
def getreviews():
    ratings = Rating.query.all()
    if not ratings:
        return jsonify({"error": "No ratings found"}), 404
    ratings_data = []
    for rating in ratings:
        if rating.rating>=3:
            ratings_data.append({
                'id':rating.id,
                'review':rating.review,
                'rating':rating.rating,
                'servicename':rating.professional.servicename,
                'cutomer':rating.user.name})
    return jsonify({'reviews': ratings_data})
            


@app.route("/get/rating/<int:user_id>", methods=["GET"])
@jwt_required()
def getrating(user_id):
    if get_jwt_identity()["role"] == "customer":
        ratings = Rating.query.filter_by(user_id=user_id).all()
        if not ratings:
            return jsonify({"error": "No ratings found"}), 404
        ratings_data = []
        for rating in ratings:
            ratings_data.append({
                'id':rating.id,
                'professionalid':rating.professional_id,
                'servicename':rating.professional.servicename,
                'servicetype':rating.professional.servicetype.servicetype,
                'address':rating.booking.address,
                'completiondate':rating.booking.updated_at.strftime('%Y-%m-%d'),
                'rating':rating.rating,
                'review':rating.review,
            })
        return jsonify({'ratings':ratings_data}),200

@app.route("/get/all/ratings",methods=['GET'])
@jwt_required()
def getallratings():    
    if get_jwt_identity()["role"] == "admin":
        ratings = Rating.query.all()
        if not ratings:
            return jsonify({"error": "No ratings found"}), 404
        ratings_data = []
        for rating in ratings:
            ratings_data.append({
                'id':rating.id,
                'professionalid':rating.professional_id,
                'servicename':rating.professional.servicename,
                'servicetype':rating.professional.servicetype.servicetype,
                'completiondate':rating.booking.updated_at.strftime('%Y-%m-%d'),
                'address':rating.booking.address,
                'rating':rating.rating,
                'review':rating.review,
                'customer':rating.user.name
            })
        return jsonify({'ratings':ratings_data}),200
    else:
        return jsonify({"error": "Unauthorized access"}), 401

@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    response = jsonify({"message":"Logged out successfully"})
    unset_jwt_cookies(response)
    return response, 200


@app.route("/admin/report",methods=['GET'])
@jwt_required()
def adminreport():
    if get_jwt_identity()["role"] == "admin":
        totalamount = 0
        bk = Booking.query.all()
        for b in bk:
            totalamount = b.booking_charge + totalamount
        return jsonify({
            "totalamount":totalamount,
            'totalbookings':len(bk),
            }),200
        
@app.route("/admin/bar/graph",methods=['GET'])

def adminbargraph():
    
    servicetypes = Servicetypes.query.all()
    ordercount = {}
    

    for servicetype in servicetypes:
        count = Booking.query.filter_by(servicetype_id=servicetype.id).count()
        ordercount[servicetype.servicetype] = count 
    service_types = list(ordercount.keys())  # Get the list of service types (keys)
    order_counts = list(ordercount.values())
    plt.figure(figsize=(10, 6))
    plt.bar(service_types,order_counts)
    plt.xlabel('Service Types')
    plt.ylabel('Number of Bookings')
    plt.title('Service Types vs Bookings')
    plt.xticks(rotation=45)
    plt.tight_layout()
    imgbar = io.BytesIO()
    plt.savefig(imgbar, format='png')
    plt.close()
    imgbar.seek(0)
    return send_file(imgbar, mimetype='image/png')


    

@app.route("/admin/pie/graph",methods=['GET'])

def adminpiegraph():    
  
    bookings={}
    bk = Booking.query.all()
    for b in bk:
        if b.status in bookings:
            bookings[b.status] += 1
        else:
            bookings[b.status] = 1
    labels = list(bookings.keys())
    values = list(bookings.values())
    plt.figure(figsize=(10, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    imgpie = io.BytesIO()
    plt.savefig(imgpie, format='png')
    plt.close()
    imgpie.seek(0)
    return send_file(imgpie, mimetype='image/png')

@app.route("/generate/report",methods=['GET'])
def generatereport():
    bookings=Booking.query.all()
    csvbuffer = io.StringIO()
    csvwriter = csv.writer(csvbuffer)
    csvwriter.writerow(['ID','customer','Service Type','Service','Service Date','Address','Booking Charge','Status'])
    for b in bookings:
        csvwriter.writerow([b.id,b.user.name,b.servicetype.servicetype,b.professional.servicename,b.service_date.strftime('%Y-%m-%d'),b.address,b.booking_charge,b.status])
   
    return csvbuffer.getvalue()
@app.route("/get/download/report",methods=['GET'])
def getdownloadreport():
    csv_file = generatereport()
    return Response(
        csv_file,mimetype="text/csv",headers={"Content-Disposition": "attachment; filename=report.csv"},)


if __name__=="__main__":
    app.run(debug=True)
