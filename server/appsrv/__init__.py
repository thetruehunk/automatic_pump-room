from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask import redirect, request, jsonify, render_template
from appsrv.data_model import db, Card, Task
from apscheduler.schedulers.background import BackgroundScheduler


handler = RotatingFileHandler("log/server.log", maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
handler.setFormatter(
    logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db/data.db3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
app.logger.addHandler(handler)

scheduler = BackgroundScheduler()

# TODO https://flask-httpauth.readthedocs.io/en/latest/
# Сделать секьюрненько
auth = HTTPBasicAuth()
users = {"trekbit": generate_password_hash("123456")}


@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    else:
        app.logger.info("username or password wrong")


@app.route("/", methods=["GET"])
@auth.login_required
def home():
    cards = [dict(row.__dict__) for row in Card.query.all()]
    app.logger.info(f"requested home page")
    return render_template("index.html", data=cards)


@app.route("/analytics", methods=["GET"])
@auth.login_required
def analytics():
    app.logger.info(f"requested analytics page")
    return render_template("analytics.html")


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
    card = Card.query.filter(Card.card_id == post_data["card_id"]).first()
    card.total_limit = int(post_data["total_limit"])
    card.total_left = int(post_data["total_limit"])
    card.daily_limit = int(post_data["daily_limit"])
    card.daily_left = int(post_data["daily_limit"])
    card.water_type = int(post_data["water_type"])
    card.date_init = post_data["date_init"]
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
        db_backup()
        scheduler.start()


scheduler.add_job(reset_daily_limit, "cron", day="*", hour=23, minute=59)
check_status_task()
