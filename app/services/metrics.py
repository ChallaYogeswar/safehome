from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from flask import Response
import time
from functools import wraps

request_count = Counter(
    'safehome_requests_total',
    'Total request count',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'safehome_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

active_users = Gauge(
    'safehome_active_users',
    'Number of active users'
)

active_cameras = Gauge(
    'safehome_active_cameras',
    'Number of active cameras'
)

detections_total = Counter(
    'safehome_detections_total',
    'Total detections',
    ['camera_id', 'detection_type']
)

alerts_total = Counter(
    'safehome_alerts_total',
    'Total alerts',
    ['severity', 'alert_type']
)

anomalies_detected = Counter(
    'safehome_anomalies_detected',
    'Total anomalies detected',
    ['camera_id']
)

ml_inference_duration = Histogram(
    'safehome_ml_inference_duration_seconds',
    'ML inference duration in seconds',
    ['model_type']
)

def track_request_metrics(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        response = f(*args, **kwargs)
        
        duration = time.time() - start_time
        
        from flask import request
        request_duration.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).observe(duration)
        
        status = getattr(response, 'status_code', 200)
        request_count.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            status=status
        ).inc()
        
        return response
    
    return decorated_function

def track_detection(camera_id, detection_type):
    detections_total.labels(
        camera_id=str(camera_id),
        detection_type=detection_type
    ).inc()

def track_alert(severity, alert_type):
    alerts_total.labels(
        severity=severity,
        alert_type=alert_type
    ).inc()

def track_anomaly(camera_id):
    anomalies_detected.labels(
        camera_id=str(camera_id)
    ).inc()

def track_ml_inference(model_type, duration):
    ml_inference_duration.labels(
        model_type=model_type
    ).observe(duration)

def update_active_users(count):
    active_users.set(count)

def update_active_cameras(count):
    active_cameras.set(count)

def metrics_endpoint():
    return Response(generate_latest(REGISTRY), mimetype='text/plain')
