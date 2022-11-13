from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, redirect, request, jsonify, render_template, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_bcrypt import Bcrypt
from appsrv.data_model import db, Card, User, Task
from apscheduler.schedulers.background import BackgroundScheduler


handler = RotatingFileHandler("log/server.log", maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
handler.setFormatter(
    logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db/data.db3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "em93jU3fnI(n2fu83jK3jf1J4$3*2n123J#1334f"
db.init_app(app)
app.logger.addHandler(handler)

scheduler = BackgroundScheduler()
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class LoginForm(FlaskForm):
    name = StringField("Логин", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


@login_manager.user_loader
def load_user(user_id):
    # return User.query.get(user_id)
    return User.query.filter(User.name == user_id).one()


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.name == form.name.data).one()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                user.authenticated = True
                db.session.commit()
                login_user(user, remember=True)
                # return redirect(next or url_for('/'))
                return redirect(url_for("home"))
    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    user = User.query.filter(User.name == current_user.name).one()
    user.authenticated = False
    db.session.commit()
    logout_user()
    return redirect(url_for("login"))


@app.route("/settings", methods=["GET"])
@login_required
def settings():
    if current_user.name == "admin":
        users = [dict(row.__dict__) for row in User.query.all()]
        return render_template(
            "settings.html", users=users, current_user=current_user.name
        )
    return redirect(url_for("home"))


@app.route("/set_settings", methods=["POST"])
@login_required
def set_settings():
    if current_user.name == "admin":
        settings_data = request.json
        user = User.query.get(settings_data["id"])
        if settings_data["enabled"] == "on":
            user.enabled = True
        else:
            user.enabled = False
        user.name = settings_data["name"]
        user.password = bcrypt.generate_password_hash(
            (settings_data["password"]).encode("utf-8")
        )
        db.session.commit()
    return redirect(url_for("settings"))


@app.route("/", methods=["GET"])
@login_required
def home():
    cards = [dict(row.__dict__) for row in Card.query.all()]
    users = {}
    for row in [row.serialized for row in User.query.all()]:
        users[row["id"]] = row["name"]
    app.logger.info(f"requested home page")
    return render_template(
        "index.html", cards=cards, users=users, current_user=current_user.name
    )


@app.route("/analytics", methods=["GET"])
@login_required
def analytics():
    app.logger.info(f"requested analytics page")
    return render_template("analytics.html")


@app.route("/api/v1/users/add_user", methods=["GET"])
@login_required
def add_user():
    if current_user.name == "admin":
        user = User(name="new_user", password="123456", enabled=False)
        db.session.add(user)
        db.session.commit()
    return redirect(url_for("settings"))


@app.route("/api/v1/resources/get_cards", methods=["GET"])
def get_cards():
    return jsonify({"data": [row.serialized for row in Card.query.all()]})


@app.route("/api/v1/resources/get_card", methods=["GET"])
def get_card():
    card_id = request.args.get("card_id")
    return jsonify(
        {"data": [row.serialized for row in Card.query.filter(Card.card_id == card_id)]}
    )


@app.route("/api/v1/resources/add_card", methods=["GET"])
def add_card():
    pass


@app.route("/api/v1/resources/update_card", methods=["POST"])
def update_card():
    post_data = request.json
    card = Card.query.filter(Card.card_id == post_data["card_id"]).first()
    card.total_left = post_data["total_left"]
    card.daily_left = post_data["daily_left"]
    card.realese_count = post_data["realese_count"]
    db.session.commit()
    app.logger.info(f"updated card {post_data}")
    # micropython not support redirect
    return jsonify({"response": "OK"})


@app.route("/api/v1/resources/set_card", methods=["POST"])
def set_card():
    post_data = request.json
    user_id = current_user.id
    card = Card.query.filter(Card.card_id == post_data["card_id"]).first()
    card.total_limit = int(post_data["total_limit"])
    card.total_left = int(post_data["total_limit"])
    card.daily_limit = int(post_data["daily_limit"])
    card.daily_left = int(post_data["daily_limit"])
    card.water_type = int(post_data["water_type"])
    card.date_init = post_data["date_init"]
    card.user_who_init = int(user_id)
    card.realese_count = 0
    db.session.commit()
    app.logger.info(f"set limits for card {post_data}")
    return redirect("/", code=303, Response=None)


def db_backup():
    with app.app_context():
        database = db.engine.raw_connection()
        current_date = datetime.now()
        with open(f"db/backup/{current_date}.sql", "w") as dump:
            for line in database.iterdump():
                dump.write("%s\n" % line)
        dump.close()
        app.logger.info("create backup")


def reset_daily_limit():
    with app.app_context():
        for row in Card.query.all():
            row.daily_left = row.daily_limit
        db.session.commit()
        app.logger.info("daily limits is reset")
        db_backup()


def check_status_task():
    app.logger.info("run check_status_task")
    with app.app_context():
        current_date = datetime.now().date()
        task = Task.query.order_by(Task.id.desc()).first()
        if task is not None:
            if current_date > task.create_date:
                if task.completed:
                    db.session.add(Task(create_date=current_date))
                    app.logger.info("previous task completed, just added new task")
                else:
                    task.completed = True
                    db.session.add(Task(create_date=current_date))
                    app.logger.info(
                        "previous task not completed, status changed and added new task"
                    )
            else:
                app.logger.info("found todays task, just run scheduler")
        else:
            db.session.add(Task(create_date=current_date))
            reset_daily_limit()
            app.logger.info("did not find today's task and completed task")
        db.session.commit()
        scheduler.start()


scheduler.add_job(reset_daily_limit, "cron", day="*", hour=23, minute=59)
check_status_task()
