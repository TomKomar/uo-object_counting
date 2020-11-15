"""
Helper functions used to train images classificator and run the classification
"""

from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from collections import Counter
from skimage import feature
import imutils.paths
import statistics
import imutils
import copy
import cv2
import os


def remove_strange_images(folder: str, after=0, before=240000, check=True):
    """
    Removes images that are:
    - smaller than mean size of an image in the whole folder
    - NoneType
    - gray (incomplete)
    - gray (gray icon with crossed camera indicating that the camera can't send an image)
    Effectively gets rid of automatically generated small 'placeholder' images saying e.g. 'Image not available'
    :param folder: folder with images to check
    :param after: remove from the list images which were taken before that time, e.g. 7AM is 70000, 7PM is 190000
    :param before:  remove from the list images which were taken after that time
    :return: list of paths to images that satisfy set requirements
    """
    image_sizes = []
    for path in imutils.paths.list_images(folder):
        if check:
            if after != 0 or before != 240000:                          # check if image was taken in set time range
                image_time = int(os.path.basename(path)[:-4])           # only if at least one of the range's boundaries
                if after < image_time < before:                         # has been set
                    is_ok, image_size = check_if_image_is_ok(path)
                else:
                    is_ok = False
            else:
                is_ok, image_size = check_if_image_is_ok(path)
            if check and is_ok:
                image_sizes.append(image_size)
        else:
            img = cv2.imread(path)
            height = int(img.shape[0])
            width = int(img.shape[1])
            image_size = (path, width, height)
            image_sizes.append(image_size)
    image_widths = [x[-2] for x in image_sizes]
    image_heights = [x[-1] for x in image_sizes]
    mean_width = statistics.median(image_widths)
    mean_height = statistics.median(image_heights)
    images_list = [image for image in image_sizes if image[1]==mean_width and image[2]==mean_height]
    return images_list


def check_if_image_is_ok(path_to_img: str, image=[]):
    """
    checks if image complies with set requirements
    :param path_to_img:
    :return:
    """
    is_ok = False
    image_size = None
    if type(image) == list:
        with open(path_to_img, 'rb') as f:
            check_chars = f.read()[-2:]
        if check_chars == b'\xff\xd9':
            img = cv2.imread(path_to_img)
            img_height = img.shape[0]
            bottom_part = (int(img_height / 4) * 3)
            img_bottom = img[bottom_part:, :]
            bottom_brightness = image_brightness(img_bottom)
            full_brightness = image_brightness(img)
            # deal with grey images and 'camera-offline' images
            if not 127.8 < bottom_brightness < 128.2 and \
                    not (147.5 < bottom_brightness < 149.5 and 172.5 < full_brightness < 174):
                height = int(img.shape[0])
                width = int(img.shape[1])
                image_size = (path_to_img, width, height)
                is_ok = True
        return is_ok, image_size
    else:
        img = image.copy()
        img_height = img.shape[0]
        bottom_part = (int(img_height / 4) * 3)
        img_bottom = img[bottom_part:, :]
        bottom_brightness = image_brightness(img_bottom)
        full_brightness = image_brightness(img)
        # deal with grey images and 'camera-offline' images
        if not 127.8 < bottom_brightness < 128.2 and\
                not (147.5 < bottom_brightness < 149.5 and 172.5 < full_brightness < 174):
            height = int(img.shape[0])
            width = int(img.shape[1])
            image_size = (path_to_img, width, height)
            is_ok = True
    return is_ok, image_size


def image_brightness(img: object):
    """

    :param img: image as Mat (opencv image)
    :return: image's average brightness
    """
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    average_color = int(img[:, :].mean())
    return average_color


def increase_contrast(img: object):
    """
    Makes all edges much clearer
    :param img: image as Mat (opencv image)
    :return: image as Mat (opencv image) with increased contrast
    """
    lab= cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)


def extract_hog(img: object, ppc=(64, 64), cpb=(4, 4), check=True):
    """
    Feature extraction is based on the bottom 2/3 of the image
    as often during the night, otherwise clear, shapes at the top of the image are completely invisible.
    Resizes the image to a size from which it can extract enough features.
    :param cpb:
    :param ppc:
    :param img: image as Mat object (opencv image)
    :return: list of features (histograms of oriented gradients) describing that image
    """
    if check:
        if img.shape[1] != 640 or img.shape[0] != 480:
            img = cv2.resize(img, (640, 480), interpolation=cv2.INTER_LANCZOS4)
    img = increase_contrast(img)
    img_height = img.shape[0]
    if check:
        img = img[int(img_height/3):,:]
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h = feature.hog(img, orientations=4, pixels_per_cell=ppc, cells_per_block=cpb, transform_sqrt=False,
                    visualise=False, feature_vector=True)
    h = h.tolist()
    h = [int(i * 1000) for i in h]
    return h


def extract_hogs_from_path(folder_path: str, brightness_threshold=50, after=0, before=240000, ppc=(64, 64), cpb=(4, 4), check=True):
    """
    Passes the images from folder to extract_hog function and puts them all into a list
    :param cpb:
    :param ppc:
    :param folder_path: where images are stored
    :param brightness_threshold: images darker than that will be ignored (value 0-255, from black to white)
    :param after: remove from the list images which were taken before that time, e.g. 7AM is 70000, 7PM is 190000
    :param before:  remove from the list images which were taken after that time
    :return: list of lists of features, i.e. for each image it will be a list of features followed by image's path
    """
    hogs = []
    if check:
        for image_path in remove_strange_images(folder_path, after, before, check):
            img = cv2.imread(image_path[0])
            brightness = image_brightness(img)
            if brightness > brightness_threshold:
                img_features = extract_hog(img, ppc=ppc, cpb=cpb)
                img_features.append(image_path)
                hogs.append(img_features)
    else:
        for image_path in imutils.paths.list_images(folder_path):
            img = cv2.imread(image_path)
            img_features = extract_hog(img, ppc=ppc, cpb=cpb, check=False)
            img_features.append(image_path)
            hogs.append(img_features)


    return hogs


def train_cluster_predictor(features: list, clusters: int) -> object:
    """

    :param features: list of lists of features, i.e. multiple objects described by multiple features (int numbers)
    :param clusters: number of clusters to create from the list of objects
    :return: predictor model
    """
    featurez = copy.deepcopy(features)
    classifier = GaussianMixture(n_components=clusters)
    classifier = classifier.fit(featurez)

    return classifier


def predict(predictor: object, features: list):
    """

    :param predictor: model object
    :param features: features based on which the prediction will be made
    :return: predicted class
    """
    label = predictor.predict(features)
    return label

def predict_prob(predictor: object, features: list):
    """

    :param predictor: model object
    :param features: features based on which the prediction will be made
    :return: predicted class
    """
    prob = predictor._estimate_log_prob(features)
    return prob

def labels_distribution(labels: list):
    """

    :param labels: list of labels assigned to data points during clustering
    :return: three lists of (k) labels, (v) their count, (std_dev) standard deviation of their distribution (~'histogram flatness')
    """
    k = Counter(labels).keys()  # equals to list(set(words))
    v = Counter(labels).values()  # counts the elements' frequency
    std_dev = statistics.stdev(v)
    return k, v, std_dev

