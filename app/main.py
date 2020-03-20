# based on python-flask-docker-sklearn-template
import os
from flask import Flask
from flask import request
from detector import Detector
import cv2
import urllib.request
import numpy as np

model_path = os.environ['MODEL']
labels_path = os.environ['LABELS']
gpu_memory = float(os.environ['GPU_MEMORY'])
min_conf = float(os.environ['MIN_CONF'])  # minimum confidence score
W = float(os.environ['W'])
H = float(os.environ['H'])

app = Flask(__name__)
detector = Detector(model_path=model_path, labels_path=labels_path, memory=gpu_memory, H=H, W=W, minimum_confidence=min_conf)

@app.route('/isAlive')
def index():
    return "true"

@app.route('/detection/api/v1.0/count_vehicles', methods=['GET'])
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
    counts['total'] = {'count': len(detections)}

    return str(counts)

if __name__ == '__main__':
    if os.environ['ENVIRONMENT'] == 'production':
        app.run(port=80,host='0.0.0.0')
    if os.environ['ENVIRONMENT'] == 'local':
        app.run(port=5000,host='0.0.0.0')