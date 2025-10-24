from flask import Flask, render_template, request, redirect, session, url_for, abort
from werkzeug.security import generate_password_hash, check_password_hash
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import google.auth.transport.requests
import cachecontrol
import requests
import os
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///footmatch.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

if os.getenv("FLASK_ENV") == "development":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # Enable HTTP for OAuth in development. REMOVE IN PRODUCTION!

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

REDIRECT_URI = "http://127.0.0.1:5000/callback" # Update as needed for production # os.getenv("REDIRECT_URI") or 

client_config = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": [REDIRECT_URI]
    }
}

flow = Flow.from_client_config(
    client_config,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    redirect_uri=REDIRECT_URI
)


def login_is_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "google_id" not in session and "email" not in session:
            return render_template("log-in.html", error="You must be logged in to access this page.")
        return f(*args, **kwargs)
    return wrapper


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
    description = db.Column(db.String(300))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship('User', backref='games')

class GamePlayer(db.Model):
    __tablename__ = 'game_player'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))

    user = db.relationship('User', backref='joined_games')
    game = db.relationship('Game', backref='players')

@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if "email" in session:
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        name = request.form.get("name")
        surname = request.form.get("surname")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("password_confirm")

        if User.query.filter_by(email=email).first():
            error = "Email already registered."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            new_user = User(name=name, surname=surname, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session["email"] = email
            return redirect(url_for("dashboard"))

    return render_template("sign-up.html", error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session["email"] = email
            return redirect(url_for("dashboard"))
        return render_template("log-in.html", error="Invalid email or password.")
    return render_template("log-in.html")

@app.route("/google-login")
def google_login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    if not session.get("state") == request.args.get("state"):
        abort(500)
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        credentials._id_token,
        token_request,
        GOOGLE_CLIENT_ID
    )
    email = id_info.get("email")
    name = id_info.get("name")

    session["google_id"] = id_info.get("sub")
    session["email"] = id_info.get("email")
    session["name"] = id_info.get("name")
    session["picture"] = id_info.get("picture")

    user = User.query.filter_by(email=email).first()

    if not user:
        new_user = User(
            name=name.split()[0],
            surname="",
            email=email,
            password=generate_password_hash(os.urandom(16).hex())  # random password for Google user
        )
        db.session.add(new_user)
        db.session.commit()
    
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_is_required
def dashboard():
    user = User.query.filter_by(email=session.get("email")).first()
    if user:
        name = user.name
        surname = user.surname
        picture = session.get("picture") or url_for('static', filename='assets/profile-picture.png')
    else:
        name = session.get("name", "Google User")
        surname = ""
        picture = session.get("picture")
    return render_template("dashboard.html", name=name, surname=surname, email=session.get("email"), picture=picture)

@app.context_processor
def inject_user_info():
    user_picture = session.get("picture")
    default_picture = url_for('static', filename='assets/profile-picture.png')
    return dict(
        picture=user_picture or default_picture,
        email=session.get("email"),
        name=session.get("name", "User")
    )
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/create-game", methods=["GET", "POST"])
@login_is_required
def create_game():
    user = User.query.filter_by(email=session.get("email")).first()
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

        if not all([game_name, date, time, location, sports_type, player_capacity, price, age]):
            return render_template("create-game.html", error="Please fill in all required fields.")

        try:
            player_capacity = int(player_capacity)
            price = float(price)
        except ValueError:
            return render_template("create-game.html", error="Invalid capacity or price format.")

        new_game = Game(
            game_name=game_name,
            date=date,
            time=time,
            location=location,
            sports_type=sports_type,
            player_capacity=player_capacity,
            price=price,
            age=age,
            description=description,
            creator_id=user.id if user else None
        )
        db.session.add(new_game)
        db.session.commit()
        return redirect(url_for("available_games"))

    return render_template("create-game.html")

@app.route("/available-games")
@login_is_required
def available_games():
    games = Game.query.all()
    return render_template("available-games.html", games=games)

@app.route("/join-game/<int:game_id>", methods=["POST"])
@login_is_required
def join_game(game_id):
    user = User.query.filter_by(email=session.get("email")).first()
    game = Game.query.get_or_404(game_id)

    # Check if already joined
    existing = GamePlayer.query.filter_by(user_id=user.id, game_id=game.id).first()
    if existing:
        return redirect(url_for("available_games", success="You have already joined this game."))

    # Check if capacity reached
    if len(game.players) >= game.player_capacity:
        return render_template("available-games.html", games=Game.query.all(), error="This game is already full.")

    new_join = GamePlayer(user_id=user.id, game_id=game.id)
    db.session.add(new_join)
    db.session.commit()

    success_message = f"You have successfully joined {game.game_name}!"
    return redirect(url_for("available_games", success=success_message))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
