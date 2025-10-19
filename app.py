from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")


@app.route('/login')
def login():
    return render_template("log-in.html")

@app.route('/sign-up')
def sign_up():
    return render_template("sign-up.html")

@app.route("/available-games")
def available_games():
    return render_template("available-games.html")

@app.route("/create-game")
def create_game():
    return render_template("create-game.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
