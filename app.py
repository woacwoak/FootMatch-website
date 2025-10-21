from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(80), nullable=False)

@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")

        if len(email) < 3:
            error = "Your email is too short."
        elif len(password) < 6:
            error = "Your password is too short. It should contain at least 6 characters."
        elif len(password_confirm) < 6:
            error = "Your password is too short. It should contain at least 6 characters."
        elif password != password_confirm:
            error = "Passwords doesn't match!"
    return render_template("sign-up.html", error=error)

@app.route('/login')
def login():
    return render_template("log-in.html")

@app.route("/available-games")
def available_games():
    return render_template("available-games.html")

@app.route("/create-game")
def create_game():
    return render_template("create-game.html")

if __name__ == "__main__":
    app.run(debug=True)