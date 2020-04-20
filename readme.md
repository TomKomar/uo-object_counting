# uo-object_counting API
based on python-flask-docker-sklearn-template \
https://github.com/Soluto/python-flask-sklearn-docker-template
\
Simple `websockets + flask + tensorflow + sqlite` API providing counts of road users in still images available via UTMC public API https://www.netraveldata.co.uk/?page_id=9\
Organised and sorted images can be accessed at Urban Observatory UTMC CCTV portal https://api.newcastle.urbanobservatory.ac.uk/camera/
- Websockets is listening for data from 'UTMC Open Camera Feeds' on `wss://api.newcastle.urbanobservatory.ac.uk/stream`
- Image URL's are passed to (included) object detection API (`i.p.add.ress:port/detection/api/v1.0/count_objects?img_url=some_address_to_image`)
- The object detection API returns counts of objects of different types (defined by tensorflow model and associated labels)
- Camera name, timestamp (both extracted from images URL), image URL and object detection API's response are stored in sqlite file database
Application's parametrization is done via environmental variables when container is started (or can be included in Dockerfile) \
Two included Dockerfiles (`with_gpu` and `without_gpu`) can be used depending on available resources

### SETUP
#### Build
build for use with or without GPU \
`docker build . -f Dockerfile-with_gpu -t tflsk_gpu`  \
`docker build . -f Dockerfile-without_gpu -t tflsk_nogpu`

#### Starting
without GPU \
`docker run -d --rm -v /folder/to/store/sqlite/filedatabase:/some/place -e DB='/some/place/cctv_counts.db' -e ENVIRONMENT='production' -e MODEL='fig_frcnn_rebuscov-3.pb' -e LABELS='rebuscov-classes-3.pbtxt' -e GPU_MEMORY=1 -e MIN_CONF=0.33 -e W=640 -e H=480 -p 6001:80 tflsk_nogpu`

running with GPU requires nvidia-docker rather than regular docker (setting runtime depends on nvidia-docker version, either `"--runtime=nvidia"` or `"--gpus all"`)

`docker run -d --runtime=nvidia --network="host" --rm -v /folder/to/store/sqlite/filedatabase:/some/place -e DB='/some/place/cctv_counts.db' -e ENVIRONMENT='production' -e MODEL='fig_frcnn_rebuscov-1.pb' -e LABELS='rebuscov-classes-1.pbtxt' -e GPU_MEMORY=1 -e MIN_CONF=0.33 -e W=640 -e H=480 -p 6001:80 tflsk_gpu`

Parameters and environmental variables:\
- Use a mounted volume `-v` to assure data persistance
- `DB` path to file database, use in tandem with mounted volume
- `ENVIRONMENT` production/local switches port between 80/5000
- `MODEL` path to detection model (relative to main.py)
- `LABELS` path to object classes mapping
- `GPU_MEMORY` what fraction of memory to use for this application (set 1 for non-gpu machine to not try and override defaults which in some cases may cause errors)
- `MIN_CONF` minimum confidence score for object detector to accept object proposal and count it
- `W` and `H` width and height for resizing images before feeding them into detection model

### Usage
#### Object detection endpoint
call API to get counts of different types of objects in an image provide via 'image_url' parameter\
`127.0.0.1:6001/detection/api/v1.0/count_objects?img_url=https://file.newcastle.urbanobservatory.ac.uk/camera-feeds/GH_A692B1/20200319/191336.jpg`\
respose will be e.g.\
`{"car": {"count": 11}, "person": {"count": 1}, "van": {"count": 1}, "truck": {"count": 1}}`\
\
another call can request counts of objects in specified camera `camera=` or all cameras when supplied parameter is 0 (zero). Other parameter is `minutes` than will tell the API how far back from now you want to get the data for.\
\
`127.0.0.1:6001/db/api/v1.0/get_counts?camera=0&minutes=60`\
response will be e.g.\
`[{"counts": "{"car": {"count": 3}}", "camera": "GH_A167G1:V02", "url": "https://file.newcastle.urbanobservatory.ac.uk/camera-feeds/GH_A167G1/20200324/175515.jpg", "ts": "2020-03-24 17:55:15"}, {"counts": "{"car": {"count": 9}}", "camera": "GH_A167I1:V01", "url": "https://file.newcastle.urbanobservatory.ac.uk/camera-feeds/GH_A167I1/20200324/175516.jpg", "ts": "2020-03-24 17:55:16"}, {"counts": "{"car": {"count": 4}}", "camera": "GH_A167K1:V01", "url": "https://file.newcastle.urbanobservatory.ac.uk/camera-feeds/GH_A167K1/20200324/175526.jpg", "ts": "2020-03-24 17:55:26"}, {"counts": "{"car": {"count": 3}}", "camera": "GH_A184A2:V01", "url": "https://file.newcastle.urbanobservatory.ac.uk/camera-feeds/GH_A184A2/20200324/175557.jpg", "ts": "2020-03-24 17:55:57"}`\
\
... or if specifying camera (e.g. NC_B1318B1): \
\
`127.0.0.1:6001/db/api/v1.0/get_counts?camera=NC_B1318B1&minutes=5`
response: \
`[{"counts": "{}", "camera": "NC_B1318B1:V01", "url": "https://file.newcastle.urbanobservatory.ac.uk/camera-feeds/NC_B1318B1/20200324/182942.jpg", "ts": "2020-03-24 18:29:42"}, {"counts": "{"car": {"count": 1}}", "camera": "NC_B1318B1:V02", "url": "https://file.newcastle.urbanobservatory.ac.uk/camera-feeds/NC_B1318B1/20200324/183149.jpg", "ts": "2020-03-24 18:31:49"}]`\
\
Note that in response camera name has view name appended after `:`, this information comes from `api.newcastle.urbanobservatory.ac.uk/stream` provided by a separate app (image clustering) https://github.com/urbanobservatory/uo-cam2views


#### Object Detection Model
The model included in `/app/` folder is FRCNN 640x480 trained on PitchIn Rebuscov dataset (collection of ~10K traffic CCTV images), publicly available soon...