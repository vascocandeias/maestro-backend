import time
import requests
from jsoncomment import JsonComment
import json
import os
import pika

parser = JsonComment(json)

DATABASE_URL = "http://" + os.environ.get("DATABASE_SERVER", "127.0.0.1:5000")
EMAIL_URL = "http://" + os.environ.get("EMAIL_SERVER", "127.0.0.1:5002")
TIMEOUT = None # No timeout

tables = {
    "datasets": "datasets",
    "networks": "networks"
}

def get_user_table_id(user):
    return user


def download_file(user, filename, fd):
    response = requests.get(DATABASE_URL + '/' + user + '/' + filename)
    response.raise_for_status()
    fd.write(response.content)


def send_email(address, body, subject, sender):
    data = {
        "subject": subject,
        "body": body,
        "mails": [address]
    }
    result = requests.post(EMAIL_URL, json=data)
    return result


def parse_output(output):
    try:
        return parser.loads(output)
    except:
        return output


def writeOutput(item, user, id):
    response = requests.put(DATABASE_URL + '/' + user + '/results/' + id, json=item)
    if response.ok:
        return True
    return False


def upload_file(data, user, id):
    requests.post(DATABASE_URL + '/' + user + '/' + id, files={"file": data})


def get_metadata(table, user, id):
    table = tables.get(table)
    if not table:
        return None

    response = requests.get(DATABASE_URL + '/' + user + '/' + table + '/' + id)
    if response.ok:
        return response.json()
    return None


def post_metadata(table, user, requestId, datasetId, datasetName, content):
    table = tables.get(table)

    id = datasetId

    if table:
        id = requests.post(
            DATABASE_URL + '/' + user + '/' + table,
            json={
                "userId": user,
                "datasetName": datasetName,
                "requestId": requestId,
                **content
            }
        ).json().get("datasetId")

    return {
        "datasetName": datasetName,
        "datasetId": id
    }

def update_result(files, user, requestId):

    response = requests.put(
        DATABASE_URL + '/' + user + '/results/' + requestId,
        json={
            'files': files,
            'pending': False
        }
    )

    return response