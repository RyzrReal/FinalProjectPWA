import os
from flask import Flask, send_from_directory, render_template, redirect, url_for, flash, session, g
from flask import request
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
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

app.secret_key = secrets.token_hex(32) #makes a key of a scramble of characters.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///login.db' #configures database name and location
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app) #creates a database linked to the app.

#database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True) #creates an id for each user (first person to login would have 1, then next would be 2, so on and so forth and what have you)
    username = db.Column(db.String(25), unique=True, nullable=False) #creates a username coloum, sets the max characters a username can be (25)
    password_hash = db.Column(db.String(150), nullable=False) #creates a coloum where the hashed password is stored.

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


def allowed_file(filename): #dhecks if the uploaded file has an allowed exstension (.txt)
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploadteach', methods=['GET','POST'])
def uploadteach():
    #connects to the database
    if request.method == "POST":
        conn = sqlite3.connect("database/importdteach.db")
        cursor = conn.cursor()

        #these directories link the html upload fields with the 
        # faculty coloum of the table, so that the teacher name and course taught matches properly.

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

    #matches the car png foer each faculty with the correct faculty on the table.
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

        #loops through all of the uploaded files
        for field_name, faculty in teacher_files.items():
            file = request.files.get(field_name) #gets the files that were uploaded (if an english file is uploaded,
            #the field_name would be english)

            if file and file.filename != "": #checks if a file exsists and isnt left empty in the import
                for line in file: #reads each line in the file
                    line = line.decode("utf-8").strip() #uploaded files are read as raw data, the strip function removes spaces and newlines
                    #so its just read as a line of info

                    if line == "":
                        continue#if there is a blank like, it is ignored

                    parts = line.split(",") #a name and course (Tim, Metal) becomes ("Tim", "Metal") as they are split by a comma in a string

                    name = parts[0].strip() #gets first value in the list
                    course_taught = parts[1].strip() if len(parts) > 1 else "" #if a course is added it lists them, otherwise it leaves it blank only importing name
                    carcolour = teacher_car[faculty] #matches the car with the faculty

                    #imports all stripped values into the database for use
                    cursor.execute("""
                        insert into importdteach (name, faculty, course_taught, carcolour, priority)
                        values (?,?,?,?,?) """, (name, faculty, course_taught, carcolour, 1))

        #makes changes permanant and closes
        conn.commit()
        conn.close()

    #returns and redirects to the upload page
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

@app.route("/setparkingnum", methods=["POST"]) 
def spacenum(): 
    spaceamout = int(request.form["spacenum"]) #recieves the number that is input in the form
    session["spaceamout"] = spaceamout #makes the value that was input and the value that will be used the same
    session.pop("roster_made", None) #removes the prior roster so that a new one can be made
    return redirect(url_for("make_roster")) #runs the roster make func

def biweeklyrostamakea():
    conn = sqlite3.connect("database/importdteach.db") 
    conn.row_factory = sqlite3.Row #allows the rows in a db to be accessed
    cursor = conn.cursor()
    spaceamout = session.get("spaceamout", 30)

    #list of all days in the biweekyly cycle
    days = ["MonA", "TuesA", "WedA", "ThurA", "FriA", "MonB", 
            "TuesB", "WedB", "ThurB", "FriB"]

    cursor.execute("delete from roster") #deletes old roster that was showing to avoid overlap

    for day in days:
        cursor.execute("select count(*) from importdteach where priority = 1") #if all teachers have priority 0, it resets them all to 1
        available = cursor.fetchone()[0] #stores number of avaliable teachers

        if available < spaceamout:
            cursor.execute("update importdteach set priority = 1") #if no teachers have 1 prio but the roster doesnt have enough to be filled, it resets them all
        
        
        #selects from teacher db
        #only chooses teachers who have priority of 1
        #gets the teachers in a random order
        #limits to amount chosen by user selections
        cursor.execute("""
            select * from importdteach  
            where priority = 1
            order by random()
            limit ?
        """, (spaceamout,))
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

@app.route("/make_roster") #when a user visits this or it is triggered, it runs the make_roster function
def make_roster():
    if session.get("roster_made"): #Checks if a roster has been made
        return redirect(url_for("roster")) #returns said roster so that i can be viewed
    
    biweeklyrostamakea()
    session["roster_made"] = True #sets as true so that multiple rosters cannot be made (it removes the button on the html page)

    return redirect(url_for("roster"))


def create_roster_tablse(): 
    conn = sqlite3.connect("database/importdteach.db")
    cursor = conn.cursor()

    #creates a table with the data from the database to be used in the roster system, storing the day and all impoirtatnt teachert info
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

create_roster_tablse() #runs the function after its defined

@app.route("/roster")
def roster():
    day = request.args.get("day", "MonA") #automatically shows mondayA as the first day.

    conn = sqlite3.connect("database/importdteach.db")
    conn.row_factory = sqlite3.Row #allows the data to be acsessed by the value, like the name and faculty from that row
    cursor = conn.cursor()

    #gets all from the roster table where the day is whatever has been selected
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