import os
import time
import datetime
import websockets
import requests
# import asyncio
import queue
import json
import threading
import asyncio
import sqlite3

async def wsListener():
    global url_queue, imgs, asks, resps, started
    url = 'wss://api.newcastle.urbanobservatory.ac.uk/stream'
    uo_url = 'https://file.newcastle.urbanobservatory.ac.uk'
    async with websockets.connect(url) as websocket:
        while True:
            time.sleep(0.01)
            msg = await websocket.recv()
            msg = json.loads(msg)
            if "data" in msg:
                data = msg['data']
                if "brokerage" in data:
                    brokerage = data['brokerage']
                    if "broker" in brokerage:
                        broker = brokerage['broker']
                        if broker['id'] == "UTMC Open Camera Feeds":
                            camera = (brokerage['id'])
                            if ':' in camera:
                                camera = camera.split(':')[0]
                            timestamp = data['timeseries']['value']['time']
                            url = data['timeseries']['value']['data']
                            url = url.replace('public', uo_url)
                            print(datetime.datetime.now() - started, imgs, camera)
                            url_queue.put({'camera': camera, 'timestamp': timestamp, 'url': url})
                            print('URL', url)
                            imgs += 1

class CarCountingAPI(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global url_queue, imgs, asks, resps, started

        conn = sqlite3.connect("cctv_counts.db")  # or use :memory: to put it in RAM
        cursor = conn.cursor()
        check_if_table_exists = "SELECT name FROM sqlite_master WHERE type='table' AND name='cctv_counts';"
        cursor.execute(check_if_table_exists)
        recs = cursor.fetchall()
        table_exists = len(recs)
        # create a table
        if table_exists == 0:
            cursor.execute("""CREATE TABLE cctv_counts
                              (camera text, url text, ts timestamp, vehs int,
                               cyc int, ped int)
                           """)
        sqlite_insert_with_param = """INSERT INTO 'cctv_counts'
                          ('camera', 'url', 'ts', 'vehs', 'cyc', 'ped') 
                          VALUES (?, ?, ?, ?, ?, ?);"""

        port = 80
        if os.environ['ENVIRONMENT'] == 'production':
            port = 80
        if os.environ['ENVIRONMENT'] == 'local':
            port = 5000

        counting_api = 'http://127.0.0.1:{}/detection/api/v1.0/count_vehicles'.format(port)

        while True:
            # await asyncio.sleep(0.1)
            if not url_queue.empty():
                ask = url_queue.get()
                asks += 1
                url = ask['url']
                PARAMS = {'img_url': url}
                r = requests.get(url=counting_api, params=PARAMS)
                resp = r.text.replace("'", '"')

                dt = ask['url'].split('/')[-2:]
                d, t = dt
                dt = datetime.datetime(int(d[:4]), int(d[4:6]), int(d[6:8]), int(t[:2]), int(t[2:4]), int(t[4:6]))
                print(ask['camera'], dt)

                data = json.loads(resp)
                vehs = sum([v['count'] for k, v in data.items() if k not in ['person', 'cyclist']])
                cycs = sum([v['count'] for k, v in data.items() if k == 'cyclist'])
                peds = sum([v['count'] for k, v in data.items() if k == 'person'])

                data_tuple = [ask['camera'], ask['url'], str(dt), vehs, cycs, peds]
                cursor.execute(sqlite_insert_with_param, data_tuple)
                conn.commit()

                print(datetime.datetime.now() - started, asks, ask['camera'], data)
                resps += 1

url_queue = queue.Queue(1000)
started = datetime.datetime.now()
imgs, asks, resps = 0, 0, 0

counter = CarCountingAPI()

counter.start()

asyncio.get_event_loop().run_until_complete(wsListener())
counter.join()