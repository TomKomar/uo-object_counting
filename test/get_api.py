import websockets
import threading
import requests
import datetime
import asyncio
import sqlite3
import queue
import json
import time
import os


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
                            print('url', url)
                            url_queue.put({'location': location, 'datetime': dt, 'url': url})

if __name__ == '__main__':
    url_queue = queue.Queue()
    asyncio.get_event_loop().run_until_complete(wsListener())
