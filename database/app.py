from flask import Flask, request, jsonify, abort, send_file
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
import json
from operator import itemgetter
import time
import shutil

load_dotenv()

app = Flask(__name__)

MONGO_URI = 'mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017'
mongo_client = MongoClient(MONGO_URI, connect=False)
mongo = mongo_client[os.environ['MONGODB_DATABASE']]

FILES_DIR = "files"

ids = {
    "datasets": "datasetId",
    "networks": "datasetId",
    "others": "datasetId",
    "results": "requestId"
}

tables = str(list(ids.keys()))[1:-1]


@app.before_first_request
def create_files_dir():
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR)


@app.route('/<userId>/<any({}):table>/<id>'.format(tables), methods=["GET"])
def get_item(userId, table, id):

    try:
        out = mongo[table].find_one({"_id": ObjectId(id), "userId": userId})
        if table == "networks":
            table = "results"
            id = out["requestId"]
            out = mongo[table].find_one({"_id": ObjectId(id), "userId": userId})
    except Exception as e:
        print(e)
        abort(404)

    if not out:
        abort(404)

    t_end = time.time() + 25

    while time.time() < t_end and table == "results" and (not out.get("done") or out.get("pending")):
        out = mongo[table].find_one({"_id": ObjectId(id), "userId": userId})
        time.sleep(1)

    if time.time() >= t_end:
        abort(504)

    out[ids[table]] = str(out.pop("_id"))

    return out


@app.route('/<userId>/<any({}):table>'.format(tables), methods=["POST"])
def post_item(userId, table):

    data = {}

    if request.get_json():
        data = request.json
    elif request.form.get("metadata"):
        data = json.loads(request.form.get("metadata"))

    id = mongo[table].insert_one({
        "userId": userId,
        **data
    }).inserted_id

    id = str(id)

    if request.files.get("file"):
        file = request.files.get("file")
        path = os.path.join(FILES_DIR, userId)
        if not os.path.exists(path):
            os.makedirs(path)
        path = os.path.join(path, id)
        file.save(path)

    return {
        ids[table]: id
    }


@app.route('/<userId>/<any({}):table>/<id>'.format(tables), methods=["PUT"])
def update_item(userId, table, id):

    try:
        out = mongo[table].update_one({
            "_id": ObjectId(id),
            "userId": userId
        }, {
            "$set": request.json
        })
    except:
        abort(404)
        
    return {
        ids[table]: id
    }


@app.route('/<userId>', methods=["DELETE"])
def delete_user(userId):
    for table in ids.keys():
        mongo[table].delete_many({"userId": userId})
    
    path = os.path.join(FILES_DIR, userId)

    if os.path.exists(path):
        shutil.rmtree(path)

    return {}

@app.route('/<userId>/<any({}):table>/<id>'.format(tables), methods=["DELETE"])
def delete_item(userId, table, id):

    try:
        out = mongo[table].find_one_and_delete({"_id": ObjectId(id), "userId": userId})
        if table == "networks":
            out = mongo.results.find_one_and_delete({"_id": ObjectId(out["requestId"]), "userId": userId})
        if table == "results":
            print("here", out["files"]["dbn.ser"]["datasetId"])
            o = mongo.networks.find_one_and_delete({"_id": ObjectId(out["files"]["dbn.ser"]["datasetId"])})
            print(o)
    except:
        abort(404)

    if not out:
        abort(404)
    
    if out.get("files"):
        for key, file in out.get("files").items():
            os.remove(os.path.join(FILES_DIR, userId, file["datasetId"]))

    path = os.path.join(FILES_DIR, userId, id)

    if os.path.exists(path):
        os.remove(path)

    return {}, 200


@app.route('/<userId>/<any({}):table>'.format(tables), methods=["GET"])
def get_table(userId, table):

    items = list(mongo[table].find({
        "userId": userId
    }, {
        "datasetName": 1,
        "requestName": 1,
        "requestId": 1
    }))

    for item in items:
        item[ids[table]] = str(item.pop("_id"))

    return jsonify(items)


@app.route('/<userId>/<id>', methods=["GET"])
def get_file(userId, id):
    try:
        return send_file(os.path.join(FILES_DIR, userId, id))
    except:
        abort(404)


@app.route('/<userId>/<id>', methods=["POST"])
def post_file(userId, id):

    if request.files.get("file"):
        file = request.files.get("file")
        path = os.path.join(FILES_DIR, userId)
        if not os.path.exists(path):
            os.makedirs(path)
        path = os.path.join(path, id)
        file.save(path)

    return {}, 200


@app.route('/examples', methods=["GET"])
def get_examples():
    try:
        return send_file('examples/files.json')
    except:
        abort(404)

@app.route('/examples/<name>', methods=['GET'])
def get_example(name):

    with open('examples/files.json') as json_file:
        l = list(map(itemgetter("name"), json.load(json_file)))
        if name not in l:
            abort(404)
    try:
        return send_file('examples/' + name)
    except:
        abort(404)


@app.route('/methods', methods=['GET'])
def get_methods():
    methods = []
    for filename in os.listdir('methods'):
        with open(os.path.join('methods', filename)) as json_file:
            aux = json.load(json_file)
            methods.append({
                'method': aux['method'],
                'mainFile': aux['mainFile']
            })
            
    return jsonify(methods)

@app.route('/methods/<method>', methods=['GET'])
def get_method(method):
    try:
        return send_file('methods/' + method + '.json')
    except:
        abort(404)


@app.errorhandler(404)
def page_not_found(e):
    return jsonify(error=404, text=str(e)), 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)