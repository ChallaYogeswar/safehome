from celery import Celery
from app import create_app
from app.models import db, Camera, User, Detection
from app.services.anomaly_service import AnomalyDetectionService
from app.services.behavior_service import BehaviorLearningService
from app.services.alert_service import AlertService
from datetime import datetime, timedelta
import os

flask_app = create_app(os.getenv('FLASK_ENV', 'development'))

celery = Celery(
    flask_app.import_name,
    broker=flask_app.config['CELERY_BROKER_URL'],
    backend=flask_app.config['CELERY_RESULT_BACKEND']
)
celery.conf.update(flask_app.config)

class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask

anomaly_service = AnomalyDetectionService()
behavior_service = BehaviorLearningService()
alert_service = AlertService()

@celery.task(name='tasks.train_anomaly_models')
def train_anomaly_models():
    cameras = Camera.query.filter_by(is_active=True).all()
    
    results = []
    for camera in cameras:
        try:
            success = anomaly_service.train_model(camera.id, days=7)
            results.append({
                'camera_id': camera.id,
                'success': success
            })
        except Exception as e:
            results.append({
                'camera_id': camera.id,
                'success': False,
                'error': str(e)
            })
    
    return results

@celery.task(name='tasks.check_anomalies')
def check_anomalies():
    cameras = Camera.query.filter_by(is_active=True).all()
    
    anomalies_found = []
    
    for camera in cameras:
        try:
            result = anomaly_service.detect_anomaly(camera.id)
            
            if result.get('anomaly'):
                alert_service.create_alert(
                    user_id=camera.user_id,
                    alert_type='anomaly_detected',
                    title='Anomaly Detected',
                    message=f'Unusual activity pattern detected on camera: {camera.name}',
                    severity='high',
                    source=f'camera_{camera.id}',
                    metadata={
                        'camera_id': camera.id,
                        'score': result.get('score'),
                        'confidence': result.get('confidence')
                    }
                )
                
                anomalies_found.append({
                    'camera_id': camera.id,
                    'camera_name': camera.name,
                    'score': result.get('score')
                })
        
        except Exception as e:
            pass
    
    return anomalies_found

@celery.task(name='tasks.learn_user_behaviors')
def learn_user_behaviors():
    users = User.query.filter_by(is_active=True).all()
    
    results = []
    for user in users:
        try:
            pattern = behavior_service.learn_user_patterns(user.id, days=30)
            results.append({
                'user_id': user.id,
                'success': True,
                'peak_hours': pattern.get('peak_hours', [])
            })
        except Exception as e:
            results.append({
                'user_id': user.id,
                'success': False,
                'error': str(e)
            })
    
    return results

@celery.task(name='tasks.cleanup_old_detections')
def cleanup_old_detections(days=30):
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    deleted = Detection.query.filter(Detection.timestamp < cutoff).delete()
    db.session.commit()
    
    return {'deleted': deleted, 'cutoff': cutoff.isoformat()}

@celery.task(name='tasks.generate_daily_report')
def generate_daily_report(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'User not found'}
    
    yesterday = datetime.utcnow() - timedelta(days=1)
    start = yesterday.replace(hour=0, minute=0, second=0)
    end = yesterday.replace(hour=23, minute=59, second=59)
    
    cameras = Camera.query.filter_by(user_id=user_id).all()
    
    total_detections = 0
    detections_by_type = {}
    
    for camera in cameras:
        count = Detection.query.filter(
            Detection.camera_id == camera.id,
            Detection.timestamp >= start,
            Detection.timestamp <= end
        ).count()
        
        total_detections += count
    
    report = {
        'date': yesterday.strftime('%Y-%m-%d'),
        'total_detections': total_detections,
        'active_cameras': len([c for c in cameras if c.is_active]),
        'total_cameras': len(cameras)
    }
    
    return report

@celery.task(name='tasks.check_camera_health')
def check_camera_health():
    cameras = Camera.query.filter_by(is_active=True).all()
    
    inactive_cameras = []
    
    for camera in cameras:
        last_detection = Detection.query.filter_by(camera_id=camera.id)\
            .order_by(Detection.timestamp.desc())\
            .first()
        
        if last_detection:
            time_since_last = datetime.utcnow() - last_detection.timestamp
            
            if time_since_last > timedelta(hours=6):
                alert_service.create_alert(
                    user_id=camera.user_id,
                    alert_type='camera_offline',
                    title='Camera Offline',
                    message=f'Camera "{camera.name}" has not reported any activity in {time_since_last.seconds // 3600} hours',
                    severity='medium',
                    source=f'camera_{camera.id}'
                )
                
                inactive_cameras.append({
                    'camera_id': camera.id,
                    'camera_name': camera.name,
                    'last_seen': last_detection.timestamp.isoformat()
                })
    
    return inactive_cameras

@celery.task(name='tasks.process_detection_batch')
def process_detection_batch(camera_id, frames_data):
    from app.services.ml_service import MLService
    ml_service = MLService()
    
    results = []
    
    for frame_data in frames_data:
        import cv2
        import numpy as np
        import base64
        
        frame_bytes = base64.b64decode(frame_data.split(',')[1])
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        objects = ml_service.detect_objects(frame)
        
        results.append({
            'objects': objects,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    return results

@celery.task(name='tasks.send_weekly_summary')
def send_weekly_summary(user_id):
    summary = behavior_service.get_weekly_summary(user_id)
    
    if not summary:
        return {'error': 'No pattern data available'}
    
    user = User.query.get(user_id)
    
    message = f"""
Weekly Security Summary

Total Detections: {summary['total_detections']}
Busiest Day: {summary['busiest_day']}
Quietest Day: {summary['quietest_day']}

Detection Breakdown:
"""
    
    for det_type, count in summary['detection_breakdown'].items():
        message += f"- {det_type}: {count}\n"
    
    alert_service.create_alert(
        user_id=user_id,
        alert_type='weekly_summary',
        title='Weekly Security Summary',
        message=message,
        severity='low',
        source='system',
        metadata=summary
    )
    
    return summary
