import flask
from flask import redirect, request, json, jsonify, render_template, make_response
from data_model import Card, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
def home():
    Session = sessionmaker(bind=engine)
    session = Session()
    response = session.query(
        Card.card_id,
        Card.water_type,
        Card.total_limit,
        Card.day_limit,
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
        Card.day_limit,
        Card.realese_count,
    ).filter(Card.card_id == text(card_id)).first()

    session.commit()
    card["card_id"] = response.card_id
    card["water_type"] = response.water_type
    card["total_limit"] = response.total_limit
    card["day_limit"] = response.day_limit
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
    card.day_limit = post_data["day_limit"]
    card.water_type = post_data["water_type"]
    card.realese_count = post_data["realese_count"]
    session.commit()
    #headers = {"Location": "/"}
    #response = make_response("OK", 303)
    #response.headers["Location"] = "/"
    #return response
    #return redirect('/', code=303)
    return jsonify({"response": "OK"})


app.run(host='0.0.0.0')

