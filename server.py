import os
from flask import Flask, send_from_directory, render_template, redirect, url_for, session
from flask import request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

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
    password = db.Column(db.String(150), nullable=False)

    def set_password(self, password):     
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

port = int(os.environ.get("PORT", 5000))

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


@app.route('/<path:path>')
def all_routes(path):
    return redirect('/')

@app.route('/')
def login():
        if 'username' in session:
            return redirect(url_for('dashboard'))
        return render_template('login.html')

#login
@app.route('/login', methods=['POST'])
def login():
    #collects info from form and runs against db
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['username'] = username
    else:
        return render_template ('login.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()