from flask import Flask, request, jsonify, make_response, render_template, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import pika

from dotenv import load_dotenv

from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    get_jwt_identity, verify_jwt_in_request, get_jti,
    get_raw_jwt, verify_jwt_refresh_token_in_request
)

import datetime
from functools import wraps
import os
import random
import time
import requests
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", 'thisissecret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users/users.db'

load_dotenv()

db = SQLAlchemy(app)
jwt = JWTManager(app)

MESSAGE_BODY = """Hi there!

Your verification code is {{}}.
Enter this code in the webapp to activate your account.

If you have any questions, send me an email at {mail}.

Now go out there and start analysing some multivariate time series with MAESTRO!
Vasco Candeias""".format(mail=os.environ.get("MAIL"))

MESSAGE_SUBJECT = "Welcome to MAESTRO!"

DATABASE_URL = "http://" + os.environ.get("DATABASE_SERVER", "127.0.0.1:5000")
EMAIL_URL = "http://" + os.environ.get("EMAIL_SERVER", "127.0.0.1:5002")

tables = [
    "datasets",
    "networks",
    "others",
    "results"
]

tables = str(tables)[1:-1]

credentials = pika.PlainCredentials('producer', 'producer')

class User(db.Model):
    mail = db.Column(db.String(128), primary_key=True)
    password = db.Column(db.String(80), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    code = db.Column(db.Integer)


class TokenBlacklist(db.Model):
    jti = db.Column(db.String(36), primary_key=True)

@app.before_first_request
def setup_sqlalchemy():
    db.create_all()

def check_confirmed(func):
    @wraps(func)
    def decorated_function(current_user, *args, **kwargs):
        if current_user.confirmed is False:
            return jsonify({'message' : 'User not confirmed!'}), 401
        return func(current_user, *args, **kwargs)

    return decorated_function

def auth_access_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        verify_jwt_in_request()
        mail = get_jwt_identity()
        try: 
            current_user = User.query.filter_by(mail=mail).first()
        except:
            return make_response('', 401)

        return f(current_user, *args, **kwargs)

    return decorated

def auth_refresh_required(f):
    """
    View decorator - require valid refresh token
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        verify_jwt_refresh_token_in_request()
        mail = get_jwt_identity()
        try: 
            TokenBlacklist.query.filter_by(jti=get_raw_jwt()["jti"]).one()
            current_user = User.query.filter_by(mail=mail).one()
        except:
            return make_response('', 401)

        return f(current_user, *args, **kwargs)

    return decorated


def generate_refresh_token(identity):
    refresh_token = create_refresh_token(identity=identity)
    token = TokenBlacklist(jti=get_jti(refresh_token))
    try:
        db.session.add(token)
        db.session.commit()
    except:
        abort(500)

    return refresh_token


@app.route('/auth/signup', methods=['POST'])
def create_user():

    data = request.get_json()
    code = int(random.randint(100000, 999999))

    if not data or not data["mail"]:
        return make_response('Missing information', 401)

    user = User.query.filter_by(mail=data["mail"]).first()

    if user and user.confirmed:
        return make_response('User already exists', 409)

    if user:
        user.code = code
        db.session.commit()
    else:
        hashed_password = generate_password_hash(data['password'], method='sha256')
        new_user = User(mail=data['mail'], password=hashed_password, code=code)

        try:
            db.session.add(new_user)
            db.session.commit()
        except:
            return jsonify({'message' : 'Error creating user'}), 401
    
    data = {
        "subject": MESSAGE_SUBJECT,
        "body": MESSAGE_BODY.format(code),
        "mails": [data['mail']]
    }
    result = requests.post(EMAIL_URL, json=data)
    if not result:
        return jsonify({'message' : 'There was an error sending the email'}), 400

    return jsonify({'message' : 'Check your e-mail!'})


@app.route('/auth/confirm', methods=['POST'])
def confirm_email():

    data = request.get_json()

    try: 
        user = User.query.filter_by(mail=data['mail']).first()
    except:
        return jsonify({'message' : 'Wrong information!'}), 401

    if user.confirmed:
        return jsonify({'message' : 'Wrong information!'}), 401
        
    if int(data['code']) != user.code:
        return make_response('Wrong code!', 400)

    user.confirmed = True
    db.session.commit()

    return {
        "message": "SUCCESS"
    }


@app.route('/users/me', methods=['DELETE'])
@auth_access_required
@check_confirmed
def delete_user(current_user):

    requests.delete(DATABASE_URL + '/' + current_user.mail)
    db.session.delete(current_user)
    db.session.commit()

    return jsonify({'message' : 'The user has been deleted!'})


@app.route('/auth/login', methods=["POST"])
def login():

    auth = request.get_json()

    if not auth or not auth["mail"] or not auth["password"]:
        return make_response('Missing information', 401)

    user = User.query.filter_by(mail=auth["mail"]).first()

    if not user:
        return make_response('Could not verify', 401)

    if not check_password_hash(user.password, auth["password"]):
        return make_response('Could not verify', 401)

    if not user.confirmed:
        return make_response('User not confirmed', 401)

    return jsonify({
        'accessToken' : create_access_token(identity=user.mail),
        'refreshToken' : generate_refresh_token(identity=user.mail)
    })

@app.route('/auth/logout', methods=["POST"])
def logout():
    token = request.get_json().get("refresh_token")

    try: 
        result = TokenBlacklist.query.filter_by(jti=get_jti(token)).one()
    except:
        return make_response('', 401)

    db.session.delete(result)
    db.session.commit()

    return {
        "message": "SUCCESS"
    }


@app.route('/auth/refresh', methods=['POST'])
@auth_refresh_required
def refresh_api(current_user):
    """
    Get a fresh access token from a valid refresh token
    """
    try:
        access_token = create_access_token(identity=current_user.mail)
        return make_response(jsonify({
            'accessToken': access_token
        }))
    except:
        abort(403)


@app.errorhandler(404)
def page_not_found(e):
    return jsonify(error=404, text=str(e)), 404


@app.route('/<any({}):table>/<id>'.format(tables), methods=["GET", "DELETE"])
@auth_access_required
@check_confirmed
def get_data(current_user, table, id):
    response = eval('requests.' + request.method.lower())(DATABASE_URL + '/' + current_user.mail + '/' + table + '/' + id)
    return response.content, response.status_code, response.headers.items()


@app.route('/<any({}):table>'.format(tables), methods=["GET", "POST"])
@auth_access_required
@check_confirmed
def get_table(current_user, table):
    response = eval('requests.' + request.method.lower())(DATABASE_URL + '/' + current_user.mail + '/' + table, data=request.values, files=request.files)
    return response.content, response.status_code, response.headers.items()


@app.route('/<any("methods", "examples"):table>', methods=["GET"])
def get_examples(table):
    response = requests.get(DATABASE_URL + '/' + table)
    return response.content, response.status_code, response.headers.items()


@app.route('/<any("methods", "examples"):table>/<name>', methods=['GET'])
def get_example(table, name):
    response = requests.get(DATABASE_URL + '/' + table + '/' + name)
    return response.content, response.status_code, response.headers.items()


@app.route('/files/<id>', methods=['GET'])
@auth_access_required
@check_confirmed
def get_file(current_user, id):
    response = requests.get(DATABASE_URL + '/' + current_user.mail + '/' + id)
    return response.content, response.status_code, response.headers.items()


@app.route('/methods/<method>', methods=["POST"])
@auth_access_required
@check_confirmed
def make_request(current_user, method):
    event = request.get_json()

    event["userId"] = current_user.mail
    event["method"] = method
    event["address"] = current_user.mail

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(os.environ.get('RABBITMQ_SERVER'), credentials=credentials))
        channel = connection.channel()
    except Exception as e:
        abort(500)

    item = {
        'userId': event.get("userId"),
        'requestName': event.get("requestName"),
        'inputFiles': event.get("inputFiles"),
        'done': False,
        'errors': False
    }
    
    response = requests.post(
        DATABASE_URL + '/' + current_user.mail + '/results',
        json=item
    ).json()

    event["requestId"] = response["requestId"]
    
    event["link"] = os.environ.get("WEBSITE_URL")
    event["time"] = datetime.datetime.utcnow().isoformat()

    channel.basic_publish(exchange='requests',
        routing_key='requests',
        body=json.dumps(event),
        properties=pika.BasicProperties(
            delivery_mode = 2, # make message persistent
        )
    )
    return {"body": event["requestId"]}


if __name__ == '__main__':
    db.create_all()
    app.run(host="localhost", debug=True, port=5001)