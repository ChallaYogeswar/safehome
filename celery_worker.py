from app.celery_tasks import celery
import os

if __name__ == '__main__':
    celery.start()
