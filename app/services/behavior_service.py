import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from app.models import Detection, Camera, User, db
import pickle
import os

class BehaviorLearningService:
    
    def __init__(self):
        self.patterns = {}
        self.model_path = 'ml_models'
    
    def learn_user_patterns(self, user_id, days=30):
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        cameras = Camera.query.filter_by(user_id=user_id).all()
        
        user_pattern = {
            'hourly_activity': defaultdict(list),
            'daily_activity': defaultdict(list),
            'detection_types': defaultdict(int),
            'camera_usage': defaultdict(int),
            'peak_hours': [],
            'quiet_hours': [],
            'typical_objects': []
        }
        
        for camera in cameras:
            detections = Detection.query.filter(
                Detection.camera_id == camera.id,
                Detection.timestamp >= cutoff
            ).all()
            
            for detection in detections:
                hour = detection.timestamp.hour
                day = detection.timestamp.weekday()
                
                user_pattern['hourly_activity'][hour].append(1)
                user_pattern['daily_activity'][day].append(1)
                user_pattern['detection_types'][detection.detection_type] += 1
                user_pattern['camera_usage'][camera.id] += 1
                
                if detection.object_class:
                    user_pattern['typical_objects'].append(detection.object_class)
        
        hourly_counts = {h: len(v) for h, v in user_pattern['hourly_activity'].items()}
        if hourly_counts:
            avg_count = np.mean(list(hourly_counts.values()))
            user_pattern['peak_hours'] = [h for h, c in hourly_counts.items() if c > avg_count * 1.5]
            user_pattern['quiet_hours'] = [h for h, c in hourly_counts.items() if c < avg_count * 0.5]
        
        from collections import Counter
        if user_pattern['typical_objects']:
            object_counter = Counter(user_pattern['typical_objects'])
            user_pattern['typical_objects'] = [obj for obj, count in object_counter.most_common(10)]
        
        self.patterns[user_id] = user_pattern
        
        pattern_file = os.path.join(self.model_path, f'pattern_user_{user_id}.pkl')
        with open(pattern_file, 'wb') as f:
            pickle.dump(user_pattern, f)
        
        return user_pattern
    
    def predict_unusual_activity(self, user_id, camera_id, detection_type, hour):
        if user_id not in self.patterns:
            self._load_pattern(user_id)
        
        if user_id not in self.patterns:
            return {'unusual': False, 'confidence': 0.0}
        
        pattern = self.patterns[user_id]
        
        unusual_reasons = []
        confidence = 0.0
        
        if hour in pattern['quiet_hours']:
            unusual_reasons.append('Activity during typical quiet hours')
            confidence += 0.4
        
        if camera_id not in pattern['camera_usage']:
            unusual_reasons.append('Activity on rarely used camera')
            confidence += 0.3
        
        if detection_type not in pattern['detection_types']:
            unusual_reasons.append('Unusual detection type')
            confidence += 0.3
        
        is_unusual = confidence > 0.5
        
        return {
            'unusual': is_unusual,
            'confidence': min(confidence, 1.0),
            'reasons': unusual_reasons,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_activity_prediction(self, user_id):
        if user_id not in self.patterns:
            self._load_pattern(user_id)
        
        if user_id not in self.patterns:
            return None
        
        pattern = self.patterns[user_id]
        current_hour = datetime.utcnow().hour
        
        hourly_avg = {h: np.mean(v) for h, v in pattern['hourly_activity'].items() if v}
        
        expected_detections = hourly_avg.get(current_hour, 0)
        
        next_peak = None
        for peak_hour in sorted(pattern['peak_hours']):
            if peak_hour > current_hour:
                next_peak = peak_hour
                break
        
        if next_peak is None and pattern['peak_hours']:
            next_peak = min(pattern['peak_hours'])
        
        return {
            'expected_detections': int(expected_detections),
            'next_peak_hour': next_peak,
            'typical_objects': pattern['typical_objects'][:5],
            'most_active_camera': max(pattern['camera_usage'].items(), key=lambda x: x[1])[0] if pattern['camera_usage'] else None
        }
    
    def _load_pattern(self, user_id):
        pattern_file = os.path.join(self.model_path, f'pattern_user_{user_id}.pkl')
        
        if os.path.exists(pattern_file):
            with open(pattern_file, 'rb') as f:
                self.patterns[user_id] = pickle.load(f)
    
    def detect_pattern_deviation(self, user_id, current_hour_count):
        if user_id not in self.patterns:
            self._load_pattern(user_id)
        
        if user_id not in self.patterns:
            return {'deviation': False}
        
        pattern = self.patterns[user_id]
        current_hour = datetime.utcnow().hour
        
        if current_hour not in pattern['hourly_activity']:
            return {'deviation': False}
        
        historical = pattern['hourly_activity'][current_hour]
        mean = np.mean(historical)
        std = np.std(historical)
        
        if std == 0:
            return {'deviation': False}
        
        z_score = abs((current_hour_count - mean) / std)
        
        is_deviation = z_score > 2.0
        
        return {
            'deviation': is_deviation,
            'z_score': float(z_score),
            'expected': float(mean),
            'actual': current_hour_count,
            'severity': 'high' if z_score > 3 else 'medium' if z_score > 2 else 'low'
        }
    
    def get_weekly_summary(self, user_id):
        if user_id not in self.patterns:
            self._load_pattern(user_id)
        
        if user_id not in self.patterns:
            return None
        
        pattern = self.patterns[user_id]
        
        daily_avg = {day: np.mean(counts) for day, counts in pattern['daily_activity'].items() if counts}
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return {
            'busiest_day': days[max(daily_avg.items(), key=lambda x: x[1])[0]] if daily_avg else None,
            'quietest_day': days[min(daily_avg.items(), key=lambda x: x[1])[0]] if daily_avg else None,
            'daily_averages': {days[k]: float(v) for k, v in daily_avg.items()},
            'total_detections': sum(pattern['detection_types'].values()),
            'detection_breakdown': dict(pattern['detection_types'])
        }
