import requests

start_time = '2018-09-11T09:00:00Z'
end_time = '2018-09-12T10:00:00Z'
camera = 'PS191'

timeseries_source_url = 'https://api.newcastle.urbanobservatory.ac.uk/api/v2/sensors/entity?brokerage:sourceId={}'.format(camera)

ts_response = requests.get(timeseries_source_url).json()

found = False
for item in ts_response['items']:
    for k, v in item.items():
        if k == 'feed':
            for mkv in v:
                for mk, mv in mkv.items():
                    if mk == 'timeseries':
                        for tkv in mv:
                            for tk, tv in tkv.items():
                                if tk == 'timeseriesId':
                                    timeseries = tv
                                    found = True
                                    break
                            if found:
                                break
                    if found:
                        break
        if found:
            break
    if found:
        break

if found:
    timeseries_url = "https://api.newcastle.urbanobservatory.ac.uk/api/v2/sensors/timeseries/{}/historic?startTime={}&endTime={}".format(timeseries, start_time, end_time)
    ts_urls = requests.get(timeseries_url).json()
    for value in ts_urls['historic']['values']:
        img_url = value['value']
        print(img_url)
