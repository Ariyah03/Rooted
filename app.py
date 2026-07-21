import requests
from flask import Flask, redirect, render_template, request, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from cs50 import SQL

app = Flask(__name__, static_folder='static')
app.secret_key = "any_random_string_you_choose"
db = SQL("sqlite:///tracker.db")

def get_weather():
    api_key = "b63530f3edacf143a1befdb7e45ded4c"
    city = "Brooklyn Park"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        data = requests.get(url, timeout=5).json()
        main = data['weather'][0]['main'].lower()
        clouds = data['clouds']['all']
        if main == 'clouds' and clouds < 30:
            return 'clear'
        return main
    except:
        return 'clear'

@app.route("/")
@login_required
def index():
    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]
    return render_template("index.html", user=user, weather=get_weather())

@app.context_processor
def inject_weather():
    return dict(weather=get_weather())

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("Must Provide Username", 400)
        elif not password:
            return apology("Must Provide Password", 400)
        elif confirmation != password:
            return apology("Confirmation Does Not Match Password", 400)

        password_hash = generate_password_hash(password)
        try:
            db.execute("INSERT INTO users (username, hash, experience) VALUES(?, ?, ?)", username, password_hash, 0)
        except:
            return apology("Username Already Exists", 400)

        rows = db.execute("SELECT id FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("login")

@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    user_id = session["user_id"]

    if request.method == "POST" and "task" in request.form:
        task = request.form.get("task")
        db.execute("INSERT INTO tasks (user_id, task) VALUES(?, ?)", user_id, task)
        return redirect("/tasks")

    elif request.method == "POST" and "complete_id" in request.form:
        task_id = request.form.get("complete_id")
        db.execute("UPDATE tasks SET completed = 1 WHERE id = ?", task_id)
        db.execute("UPDATE users SET experience = experience + 50 WHERE id = ?", user_id)
        return redirect("/tasks")

    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ? AND completed = 0", user_id)
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]
    return render_template("tasks.html", tasks=tasks, user=user)


import random

@app.route("/journal", methods=["GET", "POST"])
@login_required
def journal():
    if request.method == "POST":
        user_id = session["user_id"]
        mood = request.form.get("mood")
        question = request.form.get("question")
        answer = request.form.get("answer")
        reason = request.form.get("reason")
        tag = request.form.get("tag")

        db.execute("INSERT INTO journal (user_id, mood, question, answer, reason, tag) VALUES(?, ?, ?, ?, ?, ?)",
                   session["user_id"], mood, question, answer, reason, tag)
        db.execute("UPDATE users SET experience = experience + 40 WHERE id = ?", user_id)
        flash("Entry saved! You earned 40 EXP!")
        return redirect("/history")

    questions = ["What was the best part of your day?", "What is one goal for tomorrow?", "What is a challenge I faced today, and how did I handle it?", "What is something I am grateful for that I might have overlooked?", "Did I step outside of my comfort zone today? If so, how did it feel?", "What is one thing I could have done differently today to better support my well-being?", "What is a small victory, no matter how insignificant it might seem, that I achieved today?"]
    return render_template("journal.html", question=random.choice(questions))

@app.route("/history")
@login_required
def history():
    user_id = session["user_id"]
    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ? AND completed = 1", user_id)
    entries = db.execute("SELECT * FROM journal WHERE user_id = ? ORDER BY date DESC", user_id)

    return render_template("history.html", tasks=tasks, entries=entries)

@app.route("/analysis")
@login_required
def analysis():
    user_id = session["user_id"]
    stats = db.execute("SELECT tag, AVG(mood) as avg_mood, COUNT(*) as count FROM journal WHERE user_id = ? GROUP BY tag", user_id)
    entries = db.execute("SELECT * FROM journal WHERE user_id = ? ORDER BY date DESC", user_id)
    return render_template("analysis.html", stats=stats)




