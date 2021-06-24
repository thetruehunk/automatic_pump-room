from flask import Flask
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask import redirect, request, json, jsonify, render_template, make_response
from server.data_model import Card, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from flask_apscheduler import APScheduler


app = Flask(__name__)

class Config:
    SCHEDULER_API_ENABLED = True

scheduler = APScheduler()


# TODO https://flask-httpauth.readthedocs.io/en/latest/
# Сделать секьюрненько
auth = HTTPBasicAuth()

users = {"trekbit": generate_password_hash("123456")}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
       check_password_hash(users.get(username), password):
        return username


@app.route('/', methods=['GET'])
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
        Card.realese_count,
    ).all()

    session.commit()
    return render_template('index.html', data=response)


@app.route('/api/v1/resources/get_card', methods=['GET'])
def get_card():
    Session = sessionmaker(bind=engine)
    session = Session()
    card_id = request.args.get('card_id')
    card = {}
    response = session.query(
        Card.card_id,
        Card.water_type,
        Card.total_limit,
        Card.current_daily_limit,
        Card.realese_count,
    ).filter(Card.card_id == text(card_id)).first()

    session.commit()
    card["card_id"] = response.card_id
    card["water_type"] = response.water_type
    card["total_limit"] = response.total_limit
    card["current_daily_limit"] = response.current_daily_limit
    card["realese_count"] = response.realese_count

    return jsonify(card)


@app.route('/api/v1/resources/add_card', methods=['GET'])
def add_card():
    Session = sessionmaker(bind=engine)
    session = Session()
    card = request.args.get('card_id')


@app.route('/api/v1/resources/update_card', methods=['POST'])
def update_card():
    Session = sessionmaker(bind=engine)
    session = Session()
    post_data = request.json
    card = session.query(Card).filter(Card.card_id == text(post_data["card_id"])).first()  
    card.total_limit = post_data["total_limit"]
    card.current_daily_limit = post_data["current_daily_limit"]
    card.water_type = post_data["water_type"]
    card.realese_count = post_data["realese_count"]
    session.commit()
    
    # micropython not support redirect
    return jsonify({"response": "OK"})


@app.route('/api/v1/resources/set_card', methods=['POST'])
def set_card():
    Session = sessionmaker(bind=engine)
    session = Session()
    post_data = request.json
    card = session.query(Card).filter(Card.card_id == text(post_data["card_id"])).first()  
    card.total_limit = post_data["total_limit"]
    card.daily_limit = post_data["daily_limit"]
    card.current_daily_limit = post_data["daily_limit"]
    card.water_type = post_data["water_type"]
    card.realese_count = post_data["realese_count"]
    card.date_init = post_data["date_init"]
    session.commit()
    
    return redirect('/', code=303, Response=None)


@scheduler.task('cron', id='reset_daily_limit', day='*', hour='20', minute='01')
def reset_daily_limit():
    Session = sessionmaker(bind=engine)
    session = Session()
    for row in session.query(Card).all():
        row.current_daily_limit = row.daily_limit
    session.commit()
    print("reset limit")

if __name__ == "__main__":
    app.config.from_object(Config())
    app.config["DEBUG"] = True
    scheduler.init_app(app)
    scheduler.start()
    app.run()

