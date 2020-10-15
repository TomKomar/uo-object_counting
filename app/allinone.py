# based on python-flask-docker-sklearn-template
from detector import Detector
# from flask import request
# from flask import Flask
import urllib.request
import numpy as np
import websockets
import threading
import datetime
import psycopg2
import asyncio
import logging
import queue
import json
import time
import cv2
import os

logging.basicConfig(format = '%(asctime)s %(message)s',
                    datefmt = '%m/%d/%Y %H:%M:%S',
                    level=logging.DEBUG)

model_path = os.environ['MODEL']
labels_path = os.environ['LABELS']
gpu_memory = float(os.environ['GPU_MEMORY'])
min_conf = float(os.environ['MIN_CONF'])  # minimum confidence score
W = int(os.environ['W'])
H = int(os.environ['H'])

# app = Flask(__name__)

DB_NAME = os.environ['DB_NAME']
DB_USER = os.environ['DB_USER']
DB_PASS = os.environ['DB_PASS']
DB_DOMAIN = os.environ['DB_DOMAIN']
DB_PORT = os.environ['DB_PORT']

detector = Detector(model_path=model_path, labels_path=labels_path, memory=gpu_memory, H=H, W=W, minimum_confidence=min_conf)

async def wsListener():
    global url_queue
    url = 'wss://api.newcastle.urbanobservatory.ac.uk/stream'
    uo_url = 'https://file.newcastle.urbanobservatory.ac.uk'
    async with websockets.connect(url) as websocket:
        while True:
            time.sleep(0.01)
            msg = await websocket.recv()
            msg = json.loads(msg)
            if "data" in msg:
                data = msg['data']
                # print(data)
                if "brokerage" in data:
                    brokerage = data['brokerage']
                    if "broker" in brokerage:
                        broker = brokerage['broker']
                        if broker['id'] == "UTMC Open Camera Feeds":

                            print('pre', brokerage['id'].split(':')[0])

                            location = (brokerage['id'].split(':')[0])  # some camera name contains synthetic view name which sometimes is wrong so we get rid of that
                            print('post', location)
                            dt = data['timeseries']['value']['time']
                            url = data['timeseries']['value']['data']
                            url = url.replace('public', uo_url)
                            url_queue.put({'location': location, 'datetime': dt, 'url': url})

class Counting(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global url_queue
        DB_NAME = os.environ['DB_NAME']
        DB_USER = os.environ['DB_USER']
        DB_PASS = os.environ['DB_PASS']
        DB_DOMAIN = os.environ['DB_DOMAIN']
        DB_PORT = os.environ['DB_PORT']
        IP = os.environ['IP']

        conn = psycopg2.connect(host=DB_DOMAIN, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME)
        cursor = conn.cursor()
        sqlite_insert_counts_with_param = "INSERT INTO stills_counts VALUES (%s, %s, %s, %s);"
        sqlite_insert_counts_and_dets_with_param_dets = """INSERT INTO stills_counts_dets VALUES (?, ?, ?, ?, ?);"""

        # check_if_table_exists = "SELECT name FROM sqlite_master WHERE type='table' AND name='stills_counts';"
        # cursor.execute(check_if_table_exists)
        # recs = cursor.fetchall()
        # table_exists = len(recs)
        # # create a table
        # if table_exists == 0:
        #     cursor.execute("""CREATE TABLE stills_counts
        #                       (location text, url text, datetime timestamp, counts json)
        #                    """)
        #
        # check_if_dets_table_exists = "SELECT name FROM sqlite_master WHERE type='table' AND name='stills_counts_dets';"
        # cursor.execute(check_if_dets_table_exists)
        # recs = cursor.fetchall()
        # table_exists = len(recs)
        # # create a table
        # if table_exists == 0:
        #     cursor.execute("""CREATE TABLE stills_counts_dets
        #                       (location text, url text, datetime timestamp, counts json, dets json)
        #                    """)

        while True:
            # await asyncio.sleep(0.1)
            time.sleep(0.01)
            if not url_queue.empty():
                msg = url_queue.get()
                loc, dt, url = msg['location'], msg['datetime'], msg['url']
                counts, dets = get_prediction(url)
                print(counts, dets)
                counts = str(counts).replace("'", '"')
                dets = str(dets).replace("'", '"')

                data_tuple = [loc, url, str(dt), counts]
                print('data tuple', data_tuple)
                cursor.execute(sqlite_insert_counts_with_param, data_tuple)
                conn.commit()

                data_tuple2 = [loc, url, str(dt), counts, dets]
                print('tuple2',data_tuple2)
                cursor.execute(sqlite_insert_counts_and_dets_with_param_dets, data_tuple2)
                conn.commit()

def get_prediction(img_url):
    resp = urllib.request.urlopen(img_url)
    img = np.asarray(bytearray(resp.read()), dtype="uint8")
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (W, H))
    detections = detector.detect(img)

    counts = {}
    for det in detections:
        if det[0] in counts:
            counts[det[0]] += 1
        else:
            counts[det[0]] = 1

    dets = {}
    for det in detections:
        if det[0] in dets:
            dets[det[0]].append(det[1])
        else:
            dets[det[0]] = [det[1]]

    return counts, dets

if __name__ == '__main__':
    url_queue = queue.Queue()
    counter = Counting()
    counter.start()

    asyncio.get_event_loop().run_until_complete(wsListener())
    counter.join()
