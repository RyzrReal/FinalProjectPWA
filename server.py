import os
from flask import Flask, send_from_directory, render_template, redirect, url_for, session, g
from flask import request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import sqlite3

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
        self.password_hash = generate_password_hash(password)

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





#login
@app.route('/login', methods=['POST'])
def login():
    #collects info from form and runs against db
    username = request.form["username"]
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        return render_template ('login.html')

#register
@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template("login.html", error="User Already Has An Account")
    else:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('login'))


#logout
@app.route("/logout")
def logout():
    session.pop('username',None)
    return redirect(url_for('login'))




@app.route("/listofteach")
def listofteach():
    sort = request.args.get("sort", "name")

    conn = sqlite3.connect("database/teachers.db") 
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if sort == "name_desc":
        query = "select * from teachers order by name desc" 
    elif sort == "faculty":
        query = "select * from teachers order by faculty asc, name asc"
    elif sort == "course":
        query = "select * from teachers order by course_taught asc, name asc"
    else:
        query = "select * from teachers order by name asc" 
    
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    return render_template("listofteach.html", all_data=data, current_sort = sort)

def get_db():
    conn = sqlite3.connect("database/teachers.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teachers")
    all_data = cursor.fetchall()
    conn.close()
    return all_data

def selectionrand():
    conn = sqlite3.connect("database/teachers.db") 
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    #selects from teacher db
    #only chooses teachers who have priority of 1
    #gets the teachers in a random order
    #limits to 30 selections

    query = """
    select * from teachers  
    where priority = 1
    order by random()
    limit 30
    """  

def biweeklyrostamakea():
    conn = sqlite3.connect("database/teachers.db") 
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    #array of all days
    days = ["MonA", "TuesA", "WedA", "ThurA", "FriA", "MonB", 
            "TuesB", "WedB", "ThurB", "FriB"]

    cursor.execute("delete from roster") #deletes old roster that was showing to avoid overlap

    for day in days:
        cursor.execute("select count(*) from teachers where priority = 1") #if all teachers have priority 0, it resets them all to 1
        available = cursor.fetchone()[0]

        if available < 30:
            cursor.execute("update teachers set priority = 1") #if no teachers have 1 prio but the roster doesnt have enough to be filled, it resets them all
        #selects from teacher db
        #only chooses teachers who have priority of 1
        #gets the teachers in a random order
        #limits to 30 selections

        cursor.execute("""
            select * from teachers  
            where priority = 1
            order by random()
            limit 30
        """)
        chosenteach = cursor.fetchall()

        #save chosen teachers into  w important values and such

        for teacher in chosenteach:
            cursor.execute("""
                insert into roster (day, Teachid, name, faculty)
                values (?, ?, ?, ?)
            """, (
                day,
                teacher["Teachid"],
                teacher["name"],
                teacher["faculty"]
            ))

            #sets teacher priority to 0 so thay arent chbosen again
            cursor.execute("""
                update teachers
                set priority = 0
                where Teachid = ?
            """, (teacher["Teachid"],))

    conn.commit()
    conn.close()

@app.route("/make_roster")
def make_roster():
    biweeklyrostamakea()
    return redirect("/roster")


def create_roster_tablse():
    conn = sqlite3.connect("database/teachers.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roster (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            Teachid INTEGER,
            name TEXT,
            faculty TEXT
        )
    """)

    conn.commit()
    conn.close()

create_roster_tablse()

@app.route("/roster")
def roster():
    day = request.args.get("day", "MonA")

    conn = sqlite3.connect("database/teachers.db")
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

