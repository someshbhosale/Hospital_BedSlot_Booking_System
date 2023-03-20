from flask import Flask, json,redirect,render_template,flash,request
from flask.globals import request, session
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import select, update, delete, values
from sqlalchemy import text
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime,date
from flask_login import login_required,logout_user,login_user,login_manager,LoginManager,current_user
from flask_mail import Mail,Message
import json
import random
from pymongo import MongoClient


# mydatabase connection
local_server=True
app=Flask(__name__)
app.secret_key="RVCE"

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'EMAIL ID'
app.config['MAIL_PASSWORD'] = 'PASSWORD'
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
mail = Mail(app)






# this is for getting the unique user access
login_manager=LoginManager(app)
login_manager.login_view='login'

# // app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI']='mysql://username:password@localhost/databsename'
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/currentcoviddb'
db=SQLAlchemy(app)

#  Recommendation System
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import tensorflow as tflow
from keras.models import load_model

from nltk.stem.lancaster import LancasterStemmer
ds = pd.read_csv("HospitalsInIndia.csv")
tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 3), min_df=0, stop_words='english')
tfidf_matrix = tf.fit_transform(ds['City'])
cosine_similarities = linear_kernel(tfidf_matrix, tfidf_matrix)
results = {}

for idx, row in ds.iterrows():
    similar_indices = cosine_similarities[idx].argsort()[:-100:-1]
    similar_items = [(cosine_similarities[idx][i], ds['Hospital'][i]) for i in similar_indices] 
    results[row['Hospital']] = similar_items[1:]    
def item(id):
    return ds.loc[ds['Hospital'] == id]['City'].tolist()[0].split(' - ')[0]

def recommend(item_id, num):
    recs = results[item_id][:num]
    return recs

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or Hospitaluser.query.get(int(user_id))


class Test(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50))

	
class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    srfid=db.Column(db.String(20),unique=True)
    email=db.Column(db.String(50))
    dob=db.Column(db.String(1000))
    password=db.Column(db.String(1000))

class Hospitaluser(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20))
    email=db.Column(db.String(50))
    password=db.Column(db.String(1000))
    adminid=db.Column(db.String(20))

class Hospitaldata(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20),unique=True)
    hname=db.Column(db.String(100))
    haddress=db.Column(db.String(100))
    hphone=db.Column(db.String(100))
    normalbed=db.Column(db.Integer)
    hicubed=db.Column(db.Integer)
    icubed=db.Column(db.Integer)
    vbed=db.Column(db.Integer)

class Trig(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20))
    normalbed=db.Column(db.Integer)
    hicubed=db.Column(db.Integer)
    icubed=db.Column(db.Integer)
    vbed=db.Column(db.Integer)
    querys=db.Column(db.String(50))
    date=db.Column(db.String(50))

class Bookingpatient(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    srfid=db.Column(db.String(20))
    patientsrfid=db.Column(db.String(20))
    bedtype=db.Column(db.String(100))
    hcode=db.Column(db.String(20))
    email=db.Column(db.String(100))
    pname=db.Column(db.String(100))
    pphone=db.Column(db.String(100))
    paddress=db.Column(db.String(100))
    date=db.Column(db.String(50))

class Report(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    cost=db.Column(db.Integer)
    noofdays=db.Column(db.Integer)
    hcode=db.Column(db.String(20))
    email=db.Column(db.String(100))
    dateofdisch=db.Column(db.String(50))


@app.route("/")
def home():
    return render_template("userindex.html",current_user=current_user)

@app.route("/index")
def home1():
    return render_template("index2.html",current_user=current_user)

@app.route("/aboutus")
def aboutus():
    return render_template("/index.html",current_user=current_user)

@app.route("/trigers")
def trigers():
    query=Trig.query.all() 
    return render_template("trigers.html",query=query)


@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method=="POST":
        srfid=request.form.get('srf')
        email=request.form.get('email')
        dob=request.form.get('dob')
        password=request.form.get('password')
        encpassword=generate_password_hash(password)
        user=User.query.filter_by(srfid=srfid).first()
        emailUser=User.query.filter_by(email=email).first()
        if user or emailUser:
            flash("Email or Username is already taken","warning")
            return render_template("usersignup.html",current_user=current_user)
       
        newuser=User(srfid=srfid,email=email,dob=dob,password=encpassword)
        db.session.add(newuser)
        db.session.commit()
        msg = Message("Your Account Created Successfully!", sender='noreply@demo.com',recipients=[email])
        msg.body = ("Welcome thanks for choosing us\nYour Login Credentials Are:\n Username: {}\nPassword: {}\n\n Do not share your password\n\n\nThank You...".format(srfid,password))
        mail.send(msg)
                   
        flash("SignUp Success Please Login","success")
        return render_template("userlogin.html",current_user=current_user)

    return render_template("usersignup.html",current_user=current_user)


@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=="POST":
        srfid=request.form.get('srf')
        password=request.form.get('password')
        # print(srfid,password)
        user=User.query.filter_by(srfid=srfid).first()
        if user and check_password_hash(user.password,password):
            login_user(user)
            flash("Login Success","info")
            return render_template("userindex.html",current_user=current_user)
        else:
            flash("Invalid Credentials","danger")
            return render_template("userlogin.html",current_user=current_user)


    return render_template("userlogin.html",current_user=current_user)

@app.route('/hospitallogin',methods=['POST','GET'])
def hospitallogin():
    if request.method=="POST":
        email=request.form.get('email')
        password=request.form.get('password')
        user=Hospitaluser.query.filter_by(email=email).first()
        if user and check_password_hash(user.password,password):
            login_user(user)
            flash("Login Success","info")
            return render_template("index2.html",current_user=current_user)
        else:
            flash("Invalid Credentials","danger")
            return render_template("hospitallogin.html",current_user=current_user)


    return render_template("hospitallogin.html",current_user=current_user)

@app.route('/admin',methods=['POST','GET'])
def admin():
 
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')
        if(username=="admin" and password=="admin"):
            session['user']=username
            flash("login success","info")
            return render_template("addHosUser.html",current_user=current_user)
        else:
            flash("Invalid Credentials","danger")

    return render_template("admin.html",current_user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul","warning")
    return redirect(url_for('login'))



@app.route('/addHospitalUser',methods=['POST','GET'])
def hospitalUser():
    if('user' in session and session['user']=="admin"):
      
        if request.method=="POST":
            hcode=request.form.get('hcode')
            email=request.form.get('email')
            password=request.form.get('password') 
            adminid="admin"       
            encpassword=generate_password_hash(password)  
            hcode=hcode.upper()      
            emailUser=Hospitaluser.query.filter_by(email=email).first()
            if  emailUser:
                flash("Email is already taken","warning")
            hosuser=Hospitaluser(hcode=hcode,email=email,password=encpassword,adminid=adminid)
            db.session.add(hosuser)
            db.session.commit()
            msg = Message("Hospital User added", sender='noreply@demo.com',recipients=[email])
            msg.body = ("Welcome thanks for choosing us\nYour Login Credentials Are:\n Email Address: {}\nPassword: {}\n\nHospital Code {}\n\n Do not share your password\n\n\nThank You...".format(email,password,hcode))
            mail.send(msg)
            flash("Data Sent and Inserted Successfully","warning")
            return render_template("addHosUser.html",current_user=current_user)
    else:
        flash("Login and try Again","warning")
        return render_template("addHosUser.html",current_user=current_user)
    


# testing wheather db is connected or not  
@app.route("/test")
def test():
    try:
        a=Test.query.all()
        print(a)
        return f'MY DATABASE IS CONNECTED'
    except Exception as e:
        print(e)
        return f'MY DATABASE IS NOT CONNECTED {e}'

@app.route("/logoutadmin")
def logoutadmin():
    session.pop('user')
    flash("You are logout admin", "primary")

    return redirect('/admin')


def updatess(code):
    postsdata=Hospitaldata.query.filter_by(hcode=code).first()
    return render_template("hospitaldata.html",postsdata=postsdata)


@app.route("/recommend1",methods=['POST','GET'])
@login_required
def recommend1():
    if request.method=="POST":
        hname=request.form.get('hname')
        total=random.randint(0, 9)
        recommendations = recommend(item_id=hname, num=total+5)
        print(recommendations)
        return render_template('recommendatio.html',recommendations=recommendations)
    return render_template('recommendatio.html')

@app.route("/addhospitalinfo",methods=['POST','GET'])
def addhospitalinfo():
    email=current_user.email
    posts=Hospitaluser.query.filter_by(email=email).first()
    code=posts.hcode
    postsdata=Hospitaldata.query.filter_by(hcode=code).first()
    if request.method=="POST":
        hcode=request.form.get('hcode')
        hname=request.form.get('hname')
        haddress=request.form.get('haddress')
        hphone=request.form.get('hphone')
        nbed=request.form.get('normalbed')
        hbed=request.form.get('hicubeds')
        ibed=request.form.get('icubeds')
        vbed=request.form.get('ventbeds')
        hcode=hcode.upper()
        huser=Hospitaluser.query.filter_by(hcode=hcode).first()
        hduser=Hospitaldata.query.filter_by(hcode=hcode).first()
        if hduser:
            flash("Data is already Present you can update it..","primary")
            return render_template("hospitaldata.html",current_user=current_user)
        if huser:            
            hosdata=Hospitaldata(hcode=hcode,hname=hname,haddress=haddress,hphone=hphone,normalbed=nbed,hicubed=hbed,icubed=ibed,vbed=vbed)
            db.session.add(hosdata)
            db.session.commit()
            flash("Data Is Added","primary")
            return redirect('/addhospitalinfo')
        else:
            flash("Hospital Code not Exist","warning")
            return redirect('/addhospitalinfo')
    return render_template("hospitaldata.html",postsdata=postsdata)


@app.route("/hedit/<string:id>",methods=['POST','GET'])
@login_required
def hedit(id):
    posts=Hospitaldata.query.filter_by(id=id).first()
  
    if request.method=="POST":
        hcode=request.form.get('hcode')
        hname=request.form.get('hname')
        haddress=request.form.get('haddress')
        hphone=request.form.get('hphone')
        nbed=request.form.get('normalbed')
        hbed=request.form.get('hicubeds')
        ibed=request.form.get('icubeds')
        vbed=request.form.get('ventbeds')
        hcode=hcode.upper()
        #db.engine.execute(f"UPDATE `hospitaldata` SET `hcode` ='{hcode}',`hname`='{hname}',`normalbed`='{nbed}',`hicubed`='{hbed}',`icubed`='{ibed}',`vbed`='{vbed}' WHERE `hospitaldata`.`id`={id}")
        temp=Hospitaldata.query.filter_by(id=id).first()
        temp.hcode=hcode
        temp.hname=hname
        temp.haddress=haddress
        temp.hphone=hphone
        temp.normalbed=nbed
        temp.hicubed=hbed
        temp.icubed=ibed
        temp.vbed=vbed
        db.session.commit()
        flash("Slot Updated","info")
        return redirect("/addhospitalinfo")

    # posts=Hospitaldata.query.filter_by(id=id).first()
    return render_template("hedit.html",posts=posts)


@app.route("/hdelete/<string:id>",methods=['POST','GET'])
@login_required
def hdelete(id):
    #db.engine.execute(f"DELETE FROM `hospitaldata` WHERE `hospitaldata`.`id`={id}")
    post=Hospitaldata.query.filter_by(id=id).first()
    db.session.delete(post)
    db.session.commit()
    flash("Date Deleted","danger")
    return redirect("/addhospitalinfo")


@app.route("/pdetails",methods=['GET'])
@login_required
def pdetails():
    code=current_user.srfid
    print(code)
    data=Bookingpatient.query.filter_by(srfid=code).all()
    return render_template("detials.html",data=data)



@app.route("/patientdetails",methods=['GET'])
@login_required
def patientDetails():
    mail=current_user.email
    temp=Hospitaluser.query.filter_by(email=mail).first()
    code=temp.hcode
    data=Bookingpatient.query.filter_by(hcode=code).all()
    return render_template("patientdetails.html",data=data)


@app.route("/discharge",methods=['GET'])
@login_required
def discharge():
    mail=current_user.email
    temp=Hospitaluser.query.filter_by(email=mail).first()
    code=temp.hcode
    data=Bookingpatient.query.filter_by(hcode=code).all()
    return render_template("patientdetails.html",data=data)


@app.route("/dischargendelete/<string:patientsrfid>",methods=['POST','GET'])
@login_required
def deletendescharge(patientsrfid):
    patient=Bookingpatient.query.filter_by(patientsrfid=patientsrfid).first()
    code=patient.hcode
    #dbb=db.engine.execute(f"SELECT * FROM `hospitaldata` WHERE `hospitaldata`.`hcode`='{code}' ")        
    dbb=Hospitaldata.query.filter_by(hcode=code)
    bedtype=patient.bedtype
    if bedtype=="NormalBed":       
            for d in dbb:
                seat=d.normalbed
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.normalbed=seat+1
                db.session.commit()
                
            
    elif bedtype=="HICUBed":      
            for d in dbb:
                seat=d.hicubed
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.hicubed=seat+1
                db.session.commit()

    elif bedtype=="ICUBed":     
            for d in dbb:
                seat=d.icubed
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.icubed=seat+1
                db.session.commit()

    elif bedtype=="VENTILATORBed": 
            for d in dbb:
                seat=d.vbed
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.vbed=seat+1
                db.session.commit()
    else:
            pass
    
    admitdate=patient.date
    dateofdisch=datetime.date(datetime.now())
    noofdays=(dateofdisch-admitdate).days+1
    cost=(noofdays*500)+1000
    email=patient.email
    patientsrfid=patient.patientsrfid
    name=patient.pname
    code=patient.hcode
    newreport=Report(cost=cost,noofdays=noofdays,hcode=code,email=email,dateofdisch=dateofdisch)
    db.session.add(newreport)
    db.session.commit()
    db.session.delete(patient)
    db.session.commit()
    msg = Message("Patient Discharge Report", sender='noreply@demo.com',recipients=[email])
    msg.body = ("Thanks for choosing us.\nYour relative has been discharged from hospital.\nHere are the details\nName: {}\nSRF id: {}\nNo of days: {}\ncost: {}\n\n\nThank You...".format(name,patientsrfid,noofdays,cost))
    mail.send(msg)
    flash("has been discharged","info")
    return redirect('/patientdetails')


@app.route("/slotbooking",methods=['POST','GET'])
@login_required
def slotbooking():
    query1=Hospitaldata.query.all()
    query=Hospitaldata.query.all()
    if request.method=="POST":
        
        srfid=request.form.get('srfid')
        patientsrfid=request.form.get('patientsrfid')
        bedtype=request.form.get('bedtype')
        hcode=request.form.get('hcode')
        email=request.form.get('email')
        pname=request.form.get('pname')
        pphone=request.form.get('pphone')
        paddress=request.form.get('paddress')  
        check2=Hospitaldata.query.filter_by(hcode=hcode).first()
        checkpatient=Bookingpatient.query.filter_by(patientsrfid=patientsrfid).first()
        if checkpatient:
            flash("already srf id is registered ","warning")
            return render_template("booking.html",query=query,query1=query1)
        
        if not check2:
            flash("Hospital Code not exist","warning")
            return render_template("booking.html",query=query,query1=query1)

        code=hcode    
        dbb=Hospitaldata.query.filter_by(hcode=code)
        bedtype=bedtype
        if bedtype=="NormalBed":       
            for d in dbb:
                seat=d.normalbed
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.normalbed=seat-1
                db.session.commit()
                
            
        elif bedtype=="HICUBed":      
            for d in dbb:
                seat=d.hicubed
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.hicubed=seat-1
                db.session.commit()

        elif bedtype=="ICUBed":     
            for d in dbb:
                seat=d.icubed
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.icubed=seat-1
                db.session.commit()

        elif bedtype=="VENTILATORBed": 
            for d in dbb:
                seat=d.vbed
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.vbed=seat-1
                db.session.commit()
        else:
            pass

        check=Hospitaldata.query.filter_by(hcode=hcode).first()
        if check!=None:
            if(seat>0 and check):
                res=Bookingpatient(srfid=srfid,patientsrfid=patientsrfid,bedtype=bedtype,hcode=hcode,email=email,pname=pname,pphone=pphone,paddress=paddress,date=date.today())
                db.session.add(res)
                db.session.commit()
                flash("Slot is Booked kindly Visit Hospital for Further Procedure","success")
                return render_template("booking.html",query=query,query1=query1)
            else:
                flash("Something Went Wrong","danger")
                return render_template("booking.html",query=query,query1=query1)
        else:
            flash("Give the proper hospital Code","info")
            return render_template("booking.html",query=query,query1=query1)
            
    
    return render_template("booking.html",query=query,query1=query1)




app.run(debug=True)