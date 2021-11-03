import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask import redirect, request, jsonify, render_template
from appsrv.data_model import Card, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from flask_apscheduler import APScheduler

handler = RotatingFileHandler("log/server.log", maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
handler.setFormatter(
    logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
)

app = Flask(__name__)
app.logger.addHandler(handler)


class Config:
    SCHEDULER_API_ENABLED = True


app.config.from_object(Config())
scheduler = APScheduler()

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
    Session = sessionmaker(bind=engine)
    session = Session()
    response = session.query(
        Card.id,
        Card.card_id,
        Card.date_init,
        Card.water_type,
        Card.total_limit,
        Card.daily_limit,
        Card.current_realese_count,
    ).all()

    session.commit()

    app.logger.info(f"requested home page")

    return render_template("index.html", data=response)


@app.route("/analytics", methods=["GET"])
@auth.login_required
def analytics():
    Session = sessionmaker(bind=engine)
    session = Session()
    response = session.query(
        Card.card_id,
        Card.water_type,
        Card.date_init,
        Card.current_realese_count,
        Card.total_realese_count,
    ).all()

    session.commit()

    app.logger.info(f"requested analytics page")

    return render_template("analytics.html", data=response)


@app.route("/api/v1/resources/get_card", methods=["GET"])
def get_card():
    Session = sessionmaker(bind=engine)
    session = Session()
    card_id = request.args.get("card_id")
    card = {}
    response = (
        session.query(
            Card.card_id,
            Card.water_type,
            Card.total_limit,
            Card.current_daily_limit,
            Card.current_realese_count,
            Card.total_realese_count,
        )
        .filter(Card.card_id == text(card_id))
        .first()
    )

    session.commit()
    card["card_id"] = response.card_id
    card["water_type"] = response.water_type
    card["total_limit"] = response.total_limit
    card["current_daily_limit"] = response.current_daily_limit
    card["current_realese_count"] = response.current_realese_count
    card["total_realese_count"] = response.total_realese_count

    app.logger.info(f"requested data for card number: {card}")

    return jsonify(card)


@app.route("/api/v1/resources/add_card", methods=["GET"])
def add_card():
    Session = sessionmaker(bind=engine)
    session = Session()
    card = request.args.get("card_id")


@app.route("/api/v1/resources/update_card", methods=["POST"])
def update_card():
    Session = sessionmaker(bind=engine)
    session = Session()
    post_data = request.json
    card = (
        session.query(Card).filter(Card.card_id == text(post_data["card_id"])).first()
    )
    card.total_limit = post_data["total_limit"]
    card.current_daily_limit = post_data["current_daily_limit"]
    card.current_realese_count = post_data["current_realese_count"]
    card.total_realese_count = post_data["total_realese_count"]
    session.commit()
    # micropython not support redirect
    app.logger.info(f'updated card {post_data}')

    return jsonify({"response": "OK"})


@app.route("/api/v1/resources/set_card", methods=["POST"])
def set_card():
    Session = sessionmaker(bind=engine)
    session = Session()
    post_data = request.json
    card = (
        session.query(Card).filter(Card.card_id == text(post_data["card_id"])).first()
    )
    card.total_limit = post_data["total_limit"]
    card.daily_limit = post_data["daily_limit"]
    card.current_daily_limit = post_data["daily_limit"]
    card.water_type = post_data["water_type"]
    card.current_realese_count = 0
    card.date_init = post_data["date_init"]
    session.commit()

    app.logger.info(f'set limits for card {post_data}')

    return redirect("/", code=303, Response=None)


@scheduler.task("cron", id="reset_daily_limit", day="*", hour="8", minute="24")
def reset_daily_limit():
    Session = sessionmaker(bind=engine)
    session = Session()
    for row in session.query(Card).all():
        row.current_daily_limit = row.daily_limit
    session.commit()
    app.logger.info("daily limits is reset")


scheduler.init_app(app)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)
