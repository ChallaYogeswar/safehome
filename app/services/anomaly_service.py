import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
import os
from datetime import datetime, timedelta
from app.models import Detection, Camera, db
from collections import defaultdict

class AnomalyDetectionService:
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.model_path = 'ml_models'
        self.contamination = 0.1
        
    def extract_features(self, camera_id, window_hours=24):
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        
        detections = Detection.query.filter(
            Detection.camera_id == camera_id,
            Detection.timestamp >= cutoff
        ).order_by(Detection.timestamp.asc()).all()
        
        if len(detections) < 10:
            return None
        
        hourly_counts = defaultdict(int)
        object_counts = defaultdict(int)
        confidence_scores = []
        
        for detection in detections:
            hour = detection.timestamp.hour
            hourly_counts[hour] += 1
            
            if detection.object_class:
                object_counts[detection.object_class] += 1
            
            if detection.confidence:
                confidence_scores.append(detection.confidence)
        
        features = []
        
        for hour in range(24):
            features.append(hourly_counts.get(hour, 0))
        
        features.extend([
            len(detections),
            np.mean(confidence_scores) if confidence_scores else 0,
            np.std(confidence_scores) if confidence_scores else 0,
            len(object_counts),
            max(hourly_counts.values()) if hourly_counts else 0,
            min(hourly_counts.values()) if hourly_counts else 0
        ])
        
        return np.array(features).reshape(1, -1)
    
    def train_model(self, camera_id, days=7):
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        detections = Detection.query.filter(
            Detection.camera_id == camera_id,
            Detection.timestamp >= cutoff
        ).all()
        
        if len(detections) < 100:
            return False
        
        feature_sets = []
        
        for day_offset in range(days):
            start = datetime.utcnow() - timedelta(days=day_offset+1)
            end = datetime.utcnow() - timedelta(days=day_offset)
            
            day_detections = [d for d in detections if start <= d.timestamp < end]
            
            if len(day_detections) < 10:
                continue
            
            features = self._extract_day_features(day_detections)
            feature_sets.append(features)
        
        if len(feature_sets) < 3:
            return False
        
        X = np.array(feature_sets)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        model.fit(X_scaled)
        
        self.models[camera_id] = model
        self.scalers[camera_id] = scaler
        
        model_file = os.path.join(self.model_path, f'anomaly_camera_{camera_id}.pkl')
        scaler_file = os.path.join(self.model_path, f'scaler_camera_{camera_id}.pkl')
        
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        
        with open(scaler_file, 'wb') as f:
            pickle.dump(scaler, f)
        
        return True
    
    def _extract_day_features(self, detections):
        hourly_counts = defaultdict(int)
        object_counts = defaultdict(int)
        confidence_scores = []
        
        for detection in detections:
            hour = detection.timestamp.hour
            hourly_counts[hour] += 1
            
            if detection.object_class:
                object_counts[detection.object_class] += 1
            
            if detection.confidence:
                confidence_scores.append(detection.confidence)
        
        features = []
        
        for hour in range(24):
            features.append(hourly_counts.get(hour, 0))
        
        features.extend([
            len(detections),
            np.mean(confidence_scores) if confidence_scores else 0,
            np.std(confidence_scores) if confidence_scores else 0,
            len(object_counts),
            max(hourly_counts.values()) if hourly_counts else 0,
            min(hourly_counts.values()) if hourly_counts else 0
        ])
        
        return features
    
    def detect_anomaly(self, camera_id):
        if camera_id not in self.models:
            self._load_model(camera_id)
        
        if camera_id not in self.models:
            return {'anomaly': False, 'reason': 'Model not trained'}
        
        features = self.extract_features(camera_id, window_hours=24)
        
        if features is None:
            return {'anomaly': False, 'reason': 'Insufficient data'}
        
        scaler = self.scalers[camera_id]
        model = self.models[camera_id]
        
        features_scaled = scaler.transform(features)
        
        prediction = model.predict(features_scaled)[0]
        score = model.score_samples(features_scaled)[0]
        
        is_anomaly = prediction == -1
        
        return {
            'anomaly': is_anomaly,
            'score': float(score),
            'confidence': abs(float(score)),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _load_model(self, camera_id):
        model_file = os.path.join(self.model_path, f'anomaly_camera_{camera_id}.pkl')
        scaler_file = os.path.join(self.model_path, f'scaler_camera_{camera_id}.pkl')
        
        if os.path.exists(model_file) and os.path.exists(scaler_file):
            with open(model_file, 'rb') as f:
                self.models[camera_id] = pickle.load(f)
            
            with open(scaler_file, 'rb') as f:
                self.scalers[camera_id] = pickle.load(f)
    
    def get_anomaly_threshold(self, camera_id, percentile=95):
        if camera_id not in self.models:
            self._load_model(camera_id)
        
        if camera_id not in self.models:
            return None
        
        cutoff = datetime.utcnow() - timedelta(days=7)
        detections = Detection.query.filter(
            Detection.camera_id == camera_id,
            Detection.timestamp >= cutoff
        ).all()
        
        scores = []
        for day_offset in range(7):
            start = datetime.utcnow() - timedelta(days=day_offset+1)
            end = datetime.utcnow() - timedelta(days=day_offset)
            
            day_detections = [d for d in detections if start <= d.timestamp < end]
            
            if len(day_detections) < 10:
                continue
            
            features = self._extract_day_features(day_detections)
            features_scaled = self.scalers[camera_id].transform([features])
            score = self.models[camera_id].score_samples(features_scaled)[0]
            scores.append(score)
        
        if scores:
            return np.percentile(scores, percentile)
        return None
