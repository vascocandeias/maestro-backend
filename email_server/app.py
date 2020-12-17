from flask import Flask, request, jsonify
from flask_mail import Mail, Message
import requests
from dotenv import load_dotenv
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", 'thisissecret')

load_dotenv()

mail_settings = {
    'MAIL_SERVER': os.environ.get("MAIL_SERVER"),
    'MAIL_PORT': os.environ.get("MAIL_PORT"),
    'MAIL_USE_TLS': False,
    'MAIL_USE_SSL': True,
    'MAIL_USERNAME': os.environ.get("MAIL_USER"),
    'MAIL_PASSWORD': os.environ.get("MAIL_PASSWORD"),
    'MAIL_DEFAULT_SENDER': os.environ.get("MAIL_USER")
}

app.config.update(mail_settings)

mail = Mail(app)

@app.route('/', methods=['POST'])
def send_email():

    data = request.get_json()
    try:
        msg = Message(subject=data['subject'], body=data['body'], recipients=data['mails'])
        mail.send(msg)
    except Exception as e:
        print(e)
        return jsonify({'message' : 'Error sending email'}), 401

    return jsonify({'message' : 'Check your e-mail!'})


if __name__ == '__main__':
    app.run(host="localhost", debug=True, port=5002)