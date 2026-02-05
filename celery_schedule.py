from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'train-anomaly-models-daily': {
        'task': 'tasks.train_anomaly_models',
        'schedule': crontab(hour=2, minute=0),
    },
    'check-anomalies-hourly': {
        'task': 'tasks.check_anomalies',
        'schedule': crontab(minute=0),
    },
    'learn-behaviors-daily': {
        'task': 'tasks.learn_user_behaviors',
        'schedule': crontab(hour=3, minute=0),
    },
    'cleanup-old-detections-weekly': {
        'task': 'tasks.cleanup_old_detections',
        'schedule': crontab(day_of_week=0, hour=4, minute=0),
    },
    'check-camera-health-hourly': {
        'task': 'tasks.check_camera_health',
        'schedule': crontab(minute=30),
    },
}
