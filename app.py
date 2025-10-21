from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///footmatch.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    sports_type = db.Column(db.String(50), nullable=False)
    player_capacity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    age = db.Column(db.String(15), nullable=False)
    description = db.Column(db.String(300), nullable=True)

    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship('User', backref='games')



@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if "email" in session:
        return redirect(url_for("dashboard"))
    error = None
    success = None

    if request.method == "POST":
        name = request.form.get("name")
        surname = request.form.get("surname")
        email = request.form.get("email")
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")

        user = User.query.filter_by(email=email).first()
        if user:
            error = "Email address already registered. Please log in."
        elif len(email) < 3:
            error = "Your email is too short."
        elif len(password) < 6:
            error = "Your password is too short. It should contain at least 6 characters."
        elif password != password_confirm:
            error = "Passwords don't match!"
        else:
            new_user = User(name=name, surname=surname, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session["email"] = email
            return redirect(url_for("dashboard"))

    return render_template("sign-up.html", error=error, success=success)



@app.route('/login', methods=['GET','POST'])
def login():
    if "email" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session["email"] = email
            return redirect(url_for("dashboard"))
        else:
            return render_template("log-in.html", error="Invalid email or password.")
    return render_template("log-in.html")

@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect(url_for("login"))
    
    user = User.query.filter_by(email=session["email"]).first()

    if not user:
        session.clear()
        return redirect(url_for("login"))

    return render_template("dashboard.html", name=user.name, surname=user.surname, email=user.email)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/create-game", methods=["GET", "POST"])
def create_game():
    if "email" not in session:
        return render_template("log-in.html", error="You must be logged in to create a game.")
    
    user = User.query.filter_by(email=session["email"]).first()
    if not user:
        session.clear()
        return render_template("log-in.html", error="Session expired. Please log in again.")
    
    if request.method == "POST":
        game_name = request.form.get("game_name")
        date = request.form.get("date")
        time = request.form.get("time")
        location = request.form.get("location")
        sports_type = request.form.get("sports_type")
        player_capacity = request.form.get("player_capacity")
        price = request.form.get("price")
        age = request.form.get("age")
        description = request.form.get("description")

        if not game_name or not date or not time or not location or not sports_type or not player_capacity or not price or not age:
            return render_template("create-game.html", error="Please fill in all required fields.")

        try:
            player_capacity = int(player_capacity)
            price = float(price)
        except ValueError:
            return render_template("create-game.html", error="Capacity must be a number and price must be numeric.")
        
        


        new_game = Game(game_name=game_name,
                        date=date, time=time,
                        location=location,
                        sports_type=sports_type,
                        player_capacity=player_capacity,
                        price=price,
                        age=age,
                        description=description,
                        creator_id=user.id)
        
        db.session.add(new_game)
        db.session.commit()
        games = Game.query.all()
        return render_template("available-games.html", games=games, success="Game created successfully!")
    
    return render_template("create-game.html")

@app.route("/available-games")
def available_games():
    games = Game.query.all()
    return render_template("available-games.html", games=games)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)