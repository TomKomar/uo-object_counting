from object_detection.utils import label_map_util
import tensorflow as tf
import numpy as np
import cv2


class Detector:
    def __init__(self, model_path, labels_path, H, W, memory=1, minimum_confidence=0.1, bgr=False):
        num_classes = open(labels_path).read().count('item {')
        self.minimum_confidence = minimum_confidence
        labelMap = label_map_util.load_labelmap(labels_path)
        categories = label_map_util.convert_label_map_to_categories(labelMap, max_num_classes=num_classes,
                                                                    use_display_name=True)
        self.categoryIdx = label_map_util.create_category_index(categories)
        self.H = H
        self.W = W
        self.bgr = bgr
        config = tf.ConfigProto()
        if memory < 1:
            config.gpu_options.per_process_gpu_memory_fraction = memory

        model = tf.Graph()
        with model.as_default():
            graphDef = tf.GraphDef()

            with tf.gfile.GFile(model_path, "rb") as f:
                serializedGraph = f.read()
                graphDef.ParseFromString(serializedGraph)
                tf.import_graph_def(graphDef, name="")

            if memory > 0:
                self.sess = tf.Session(graph=model, config=config)
            else:
                self.sess = tf.Session(graph=model)

            self.imageTensor = model.get_tensor_by_name("image_tensor:0")
            self.boxesTensor = model.get_tensor_by_name("detection_boxes:0")

            self.scoresTensor = model.get_tensor_by_name("detection_scores:0")
            self.classesTensor = model.get_tensor_by_name("detection_classes:0")
            self.numDetections = model.get_tensor_by_name("num_detections:0")

    def detect(self, img_color):
        if self.bgr:
            img_color = cv2.cvtColor(img_color.copy(), cv2.COLOR_BGR2RGB)
        img_tensor = np.expand_dims(img_color, axis=0)

        (boxes, scores, labels, N) = self.sess.run([self.boxesTensor, self.scoresTensor, self.classesTensor, self.numDetections],
                                                  feed_dict={self.imageTensor: img_tensor})
        boxes = np.squeeze(boxes)
        scores = np.squeeze(scores)
        labels = np.squeeze(labels)
        boxez = []
        for box in boxes:
            y1, x1, y2, x2 = int(box[0]*self.H), int(box[1]*self.W), int(box[2]*self.H), int(box[3]*self.W)
            boxez.append([y1, x1, y2, x2])
        boxes = boxez
        labels = [str(self.categoryIdx[label]["name"]) for label in labels]
        labels_boxes = [[label, [box[0], box[1], box[2], box[3], round(float(score), 4)]] for box, score, label in zip(boxes, scores, labels) if score > self.minimum_confidence]
        return labels_boxes


    def detect_batch(self, images):
        images_batch = []
        for img_color in images:
            if self.bgr:
                img_color = cv2.cvtColor(img_color.copy(), cv2.COLOR_BGR2RGB)
            img_tensor = np.expand_dims(img_color, axis=0)
            images_batch.append(img_tensor)
        images_batch_tensor = np.concatenate(images_batch, axis=0)

        (boxes, scores, labels, N) = self.sess.run([self.boxesTensor, self.scoresTensor, self.classesTensor, self.numDetections],
                                                  feed_dict={self.imageTensor: images_batch_tensor})

        labels_boxes_batch = []
        for boxs, scors, labls in zip(boxes, scores, labels):
            boxez = []
            for box in boxs:
                y1, x1, y2, x2 = int(box[0]*self.H), int(box[1]*self.W), int(box[2]*self.H), int(box[3]*self.W)
                boxez.append([y1, x1, y2, x2])
            boxs = boxez
            labls = [str(self.categoryIdx[label]["name"]) for label in labls]
            labels_boxes = [[label, [box[0], box[1], box[2], box[3], round(float(score), 4)]] for box, score, label in zip(boxs, scors, labls) if score > self.minimum_confidence]
            labels_boxes_batch.append(labels_boxes)
        return labels_boxes_batch

    def close(self):
        self.sess.close()
