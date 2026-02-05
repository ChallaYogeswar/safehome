import cv2
import numpy as np
import os
from pathlib import Path

class MLService:
    
    def __init__(self):
        self.object_detector = None
        self.face_cascade = None
        self.confidence_threshold = 0.5
        self._load_models()
    
    def _load_models(self):
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        except Exception as e:
            print(f"Error loading face cascade: {e}")
        
        try:
            model_path = Path('ml_models')
            if (model_path / 'yolov3.weights').exists():
                self.object_detector = cv2.dnn.readNet(
                    str(model_path / 'yolov3.weights'),
                    str(model_path / 'yolov3.cfg')
                )
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
    
    def detect_objects(self, frame):
        if self.object_detector is None:
            return self._detect_objects_simple(frame)
        
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.object_detector.setInput(blob)
        
        layer_names = self.object_detector.getLayerNames()
        output_layers = [layer_names[i - 1] for i in self.object_detector.getUnconnectedOutLayers()]
        
        detections = self.object_detector.forward(output_layers)
        
        height, width = frame.shape[:2]
        boxes = []
        confidences = []
        class_ids = []
        
        for detection in detections:
            for obj in detection:
                scores = obj[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > self.confidence_threshold:
                    center_x = int(obj[0] * width)
                    center_y = int(obj[1] * height)
                    w = int(obj[2] * width)
                    h = int(obj[3] * height)
                    
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, 0.4)
        
        results = []
        class_names = self._get_coco_classes()
        
        for i in indices:
            idx = i if isinstance(i, int) else i[0]
            box = boxes[idx]
            results.append({
                'class': class_names[class_ids[idx]] if class_ids[idx] < len(class_names) else 'unknown',
                'confidence': confidences[idx],
                'bbox': box
            })
        
        return results
    
    def _detect_objects_simple(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        results = []
        for (x, y, w, h) in faces:
            results.append({
                'class': 'person',
                'confidence': 0.8,
                'bbox': [int(x), int(y), int(w), int(h)]
            })
        
        return results
    
    def detect_faces(self, frame):
        if self.face_cascade is None:
            return []
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        results = []
        for (x, y, w, h) in faces:
            results.append({
                'confidence': 0.9,
                'bbox': [int(x), int(y), int(w), int(h)]
            })
        
        return results
    
    def _get_coco_classes(self):
        return ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
                'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
                'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
                'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
                'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
                'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
                'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
                'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
                'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book',
                'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']
