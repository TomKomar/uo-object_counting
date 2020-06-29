#!/bin/bash
docker rm -f STILLS_COUNTER
docker run -d --restart=always --gpus device=0 -e DB_NAME=uo-vision-1 -e DB_USER=uo -e DB_PASS=vision -e DB_DOMAIN=database.urbanobservatory.ac.uk -e DB_PORT=5234 -e ENVIRONMENT='production' -e MODEL='fig_frcnn_rebuscov-3.pb' -e LABELS='rebuscov-classes-3.pbtxt' -e GPU_MEMORY=0.25 -e MIN_CONF=0.25 -e W=640 -e H=480 -e CUDA_VISIBLE_DEVICES=0 -p 6001:80 --name STILLS_COUNTER tflsk_gpu
