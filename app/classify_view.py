"""
Use a pre-trained model to classify an image
"""

from view_classification_functions import *
# import argparse
import pickle
import numpy
import json
import cv2
import os
# ap = argparse.ArgumentParser()
# ap.add_argument("-m", "--model", required=True, help="path to model")
# ap.add_argument("-i", "--image", required=True, help="path to image to classify")
# ap.add_argument("-j", "--json", default='blank', help="path to class matching file")
# args = vars(ap.parse_args())



def classify_view(model_path, img, json_path='blank'):
    # try:
    if True:
        model = pickle.load(open(model_path, 'rb'))
        the_camera = os.path.basename(model_path).split('.')[0]
        # make sure that image is of right size and content (e.g. not gray or erroneous
        # if check_if_image_is_ok(image_path)[0]:

        # img = cv2.imread(image_path)
        # prepare the features from images
        features = extract_hog(img)
        features = numpy.asarray(features)
        features = features.reshape(1, -1)

        prediction = predict(model, features)[0]
        prob = predict_prob(model, features)[0].tolist()

        # go through the contents of json file
        # looking for match on the camera name
        # and if there are 'match' and 'merge' keys
        # use them to match prediciton to
        # previous classifier and merge classes
        found_matching = 0
        found_merge = 0
        if json_path != 'blank' and os.path.isfile(json_path) and os.stat(json_path).st_size > 0:
            with open(json_path, "r") as jsonFile:
                datas = json.load(jsonFile)
                for data in datas['cameras']:
                    if data['camera'] == the_camera:
                        if 'match' in data:
                            matching = data['match']
                            found_matching = 1
                        if 'merge' in data:
                            merge = data['merge']
                            found_merge = 1
                        if found_matching:
                            for k, v in matching.items():
                                if k == prediction:
                                    prediction = v
                                    break
                        if found_merge:
                            for k, v in merge.items():
                                if k == prediction:
                                    prediction = v
                                    break
            print(prediction, prob)
            return prediction
        else:
            print(prediction, prob)
            return prediction
    else:
        prediction = -1
        return prediction
    # except Exception as e:
    #     print(e)
    #     return -1