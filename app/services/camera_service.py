import cv2
import numpy as np
from collections import defaultdict

class CameraService:
    
    def __init__(self):
        self.previous_frames = {}
        self.motion_threshold = 25
        self.min_area = 500
    
    def detect_motion(self, camera_id, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if camera_id not in self.previous_frames:
            self.previous_frames[camera_id] = gray
            return False
        
        frame_delta = cv2.absdiff(self.previous_frames[camera_id], gray)
        thresh = cv2.threshold(frame_delta, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
        
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                motion_detected = True
                break
        
        self.previous_frames[camera_id] = gray
        
        return motion_detected
    
    def get_motion_regions(self, camera_id, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if camera_id not in self.previous_frames:
            self.previous_frames[camera_id] = gray
            return []
        
        frame_delta = cv2.absdiff(self.previous_frames[camera_id], gray)
        thresh = cv2.threshold(frame_delta, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                (x, y, w, h) = cv2.boundingRect(contour)
                regions.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'area': int(cv2.contourArea(contour))
                })
        
        self.previous_frames[camera_id] = gray
        
        return regions
    
    def clear_camera_data(self, camera_id):
        if camera_id in self.previous_frames:
            del self.previous_frames[camera_id]
