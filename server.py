import os
from flask import Flask, send_from_directory, render_template, redirect, url_for, flash, session, g
from flask import request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import sqlite3
from cryptography.fernet import Fernet
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed 
from wtforms import SelectField
from werkzeug.utils import secure_filename 

UPLOAD_FOLDER = '/static/txtfileup'
ALLOWED_EXTENSIONS = {'txt'}

app = Flask(__name__)


#Db setup

app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///login.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):     
        self.password_hash = generate_password_hash(password) #this stores the password as a scramble of letters instead of the actual password

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

port = int(os.environ.get("PORT", 5000))

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html')
    return render_template('login.html')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploadteach', methods=['GET','POST'])
def uploadteach():
    #connects to the database
    if request.method == "POST":
        conn = sqlite3.connect("database/importdteach.db")
        cursor = conn.cursor()

        teacher_files = {
            "english":"English",
            "maths": "Mathematics",
            "science":"Science",
            "tas":"TAS",
            "capa":"CAPA",
            "pdhpe":"PDHPE",
            "historylanguage": "History and Languages",
            "hsie":"HSIE",
            "learningsupp":"Learning Support",
            "adminsupp":"Student Administration and Support"
        }

        teacher_car = {
            "English" : "englishcar.png",
            "Mathematics" : "mathscar.png",
            "Science" : "sciencecar.png",
            "TAS" : "tascar.png",
            "CAPA" : "capacar.png",
            "PDHPE" : "pdhpecar.png",
            "History and Languages" : "halcar.png",
            "HSIE" : "hsiecar.png",
            "Learning Support" : "lscar.png",
            "Student Administration and Support" : "saascar.png"
        }

        for field_name, faculty in teacher_files.items():
            file = request.files.get(field_name)

            if file and file.filename != "":
                for line in file:
                    line = line.decode("utf-8").strip()

                    if line == "":
                        continue

                    parts = line.split(",")

                    name = parts[0].strip()
                    course_taught = parts[1].strip() if len(parts) > 1 else ""
                    carcolour = teacher_car[faculty]


                    cursor.execute("""
                        insert into importdteach (name, faculty, course_taught, carcolour, priority)
                        values (?,?,?,?,?) """, (name, faculty, course_taught, carcolour, 1))

        conn.commit()
        conn.close()

        return redirect(url_for("uploadteach"))
    return render_template("uploadteach.html")        


#login
@app.route('/login', methods=['POST']) #creates a login route that only accepts the inputs comming from the form
def login():
    username = request.form["username"] #saves the username variable as the username input in the form
    password = request.form["password"] #saves the password variable as the password input in the form
    if not username or not password:
        return render_template("login.html", error="No username or password entered")
    
    user = User.query.filter_by(username=username).first() #checks if the username inputted is in the login.db                      ##(this prevents SQLinjection, where the username is sent as data and not just a standard 1=1 method of veryfing a password)
    if user and user.check_password(password): #checks if the username and the password_hash for said username matches in the data
        session['username'] = username #keeps user logged in by storing the username in session
        return redirect(url_for('home')) #sends user to home page (sucsessful login)
    else:
        return render_template ('login.html') #sends user to back to login page (unsucsessful login)

#register
@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"] 
    password = request.form["password"]

    if not username or not password:
        return render_template("login.html", error="No username or password entered")

    user = User.query.filter_by(username=username).first() #checks if the username is already in the database
    if user:
        return render_template("login.html", error="User Already Has An Account") #reroutes user to login page
    else:
        new_user = User(username=username) #sets the wanted username as username being stored
        new_user.set_password(password) #hashes the password for the database
        db.session.add(new_user) #adds user to db
        db.session.commit() #permanantly saves new user to db
        session['username'] = username #logs user in instantly after they register
        return redirect(url_for('login'))


#logout
@app.route("/logout")
def logout():
    session.pop('username',None) #deletes their session, logging them out
    return redirect(url_for('login'))




@app.route("/listofteach")
def listofteach():
    sort = request.args.get("sort", "name") #if the url shows that the user wants to sort by something like faculty, it uses the sort argument, otherwise it sorts by name

    #connects to the database
    conn = sqlite3.connect("database/importdteach.db") 
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    #give option to sort by name, faculty or course
    if sort == "name_desc":
        query = "select * from importdteach order by name desc" 
    elif sort == "faculty":
        query = "select * from importdteach order by faculty asc, name asc"
    elif sort == "course":
        query = "select * from importdteach order by course_taught asc, name asc"
    else:
        query = "select * from importdteach order by name asc" 
    
    #gets the sorted data and sends to the page
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    return render_template("listofteach.html", all_data=data, current_sort = sort)

def get_db():
    conn = sqlite3.connect("database/importdteach.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM importdteach")
    all_data = cursor.fetchall()
    conn.close()
    return all_data


def biweeklyrostamakea():
    conn = sqlite3.connect("database/importdteach.db") 
    conn.row_factory = sqlite3.Row #allows the rows in a db to be accessed
    cursor = conn.cursor()

    #list of all days in the biweekyly cycle
    days = ["MonA", "TuesA", "WedA", "ThurA", "FriA", "MonB", 
            "TuesB", "WedB", "ThurB", "FriB"]

    cursor.execute("delete from roster") #deletes old roster that was showing to avoid overlap

    for day in days:
        cursor.execute("select count(*) from importdteach where priority = 1") #if all teachers have priority 0, it resets them all to 1
        available = cursor.fetchone()[0] #stores number of avaliable teachers

        if available < 30:
            cursor.execute("update importdteach set priority = 1") #if no teachers have 1 prio but the roster doesnt have enough to be filled, it resets them all
        
        
        #selects from teacher db
        #only chooses teachers who have priority of 1
        #gets the teachers in a random order
        #limits to 30 selections
        cursor.execute("""
            select * from importdteach  
            where priority = 1
            order by random()
            limit 30
        """)
        chosenteach = cursor.fetchall()

        #save chosen teachers into  w important values and such

        for teacher in chosenteach:
            cursor.execute("""
                insert into roster (day, Teachid, name, faculty, carcolour, course_taught)
                values (?, ?, ?, ?, ?, ?)
            """, (
                day,
                teacher["Teachid"],
                teacher["name"],
                teacher["faculty"],
                teacher["carcolour"],
                teacher["course_taught"]
            ))

            #sets teacher priority to 0 so thay arent chbosen again
            cursor.execute("""
                update importdteach
                set priority = 0
                where Teachid = ?
            """, (teacher["Teachid"],))

    conn.commit()
    conn.close()

@app.route("/make_roster")
def make_roster():
    if session.get("roster_made"):
        return redirect(url_for("roster"))
    
    biweeklyrostamakea()
    session["roster_made"] = True

    return redirect(url_for("roster"))


def create_roster_tablse():
    conn = sqlite3.connect("database/importdteach.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roster (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            Teachid INTEGER,
            name TEXT,
            faculty TEXT,
            carcolour TEXT,
            course_taught TEXT
        )
    """)

    conn.commit()
    conn.close()

create_roster_tablse()

@app.route("/roster")
def roster():
    day = request.args.get("day", "MonA")

    conn = sqlite3.connect("database/importdteach.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM roster
        WHERE day = ?
        ORDER BY name ASC
    """, (day,))

    data = cursor.fetchall()
    conn.close()

    return render_template("roster.html", all_data=data, current_day=day)





@app.route('/<path:path>')
def all_routes(path):
    return redirect('/')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_roster_tablse()
    app.run()

