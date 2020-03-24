# based on python-flask-docker-sklearn-template
from detector import Detector
from flask import Flask
from flask import request
import urllib.request
import numpy as np
import datetime
import sqlite3
import json
import cv2
import os

model_path = os.environ['MODEL']
labels_path = os.environ['LABELS']
gpu_memory = float(os.environ['GPU_MEMORY'])
min_conf = float(os.environ['MIN_CONF'])  # minimum confidence score
W = int(os.environ['W'])
H = int(os.environ['H'])

app = Flask(__name__)

if os.environ['DB'] != 'none':
    db = os.environ['DB']
else:
    db = 'cctv_counts_json.db'

detector = Detector(model_path=model_path, labels_path=labels_path, memory=gpu_memory, H=H, W=W, minimum_confidence=min_conf)

@app.route('/isAlive')
def index():
    return "true"


@app.route('/db/api/v1.0/get_counts', methods=['GET'])
def getCounts():
    camera = request.args.get('camera')
    minutes = request.args.get('minutes')

    con = sqlite3.connect(db)
    c = con.cursor()

    dt = datetime.datetime.now() - datetime.timedelta(minutes=int(minutes))

    if camera == '0':
        c.execute("SELECT camera, url, ts, counts FROM cctv_counts_json WHERE ts BETWEEN '{}' AND '{}'".format(dt, datetime.datetime.now()))
        recs = c.fetchall()
    else:
        c.execute("SELECT camera, url, ts, counts FROM cctv_counts_json WHERE camera LIKE '%{}%' AND (ts BETWEEN '{}' AND '{}')".format(camera, dt, datetime.datetime.now()))
        recs = c.fetchall()
    c.close()
    if con:
        con.close()

    dicts = [{'camera': cam, 'url': url, 'ts': ts, 'counts': counts} for
             cam, url, ts, counts in recs]

    return str(dicts).replace("'", '"')


@app.route('/detection/api/v1.0/count_objects', methods=['GET'])
def get_prediction():
    img_url = request.args.get('img_url')
    resp = urllib.request.urlopen(img_url)
    img = np.asarray(bytearray(resp.read()), dtype="uint8")
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (W, H))
    detections = detector.detect(img)

    counts = {}
    for det in detections:
        if det[0] in counts:
            counts[det[0]]['count'] += 1
        else:
            counts[det[0]] = {'count': 1}

    resp = str(counts).replace("'", '"')
    return str(resp)

if __name__ == '__main__':
    if os.environ['ENVIRONMENT'] == 'production':
        app.run(port=80, host='0.0.0.0')
    if os.environ['ENVIRONMENT'] == 'local':
        app.run(port=5000, host='0.0.0.0')