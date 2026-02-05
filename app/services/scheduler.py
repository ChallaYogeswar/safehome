from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.models import AutomationRule, db
from app.services.rule_engine import RuleEngine
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AutomationScheduler:
    
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.rule_engine = RuleEngine()
        self.app = app
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        if not self.scheduler.running:
            self.scheduler.start()
        
        with app.app_context():
            self.load_scheduled_rules()
        
        logger.info('Automation scheduler started')
    
    def load_scheduled_rules(self):
        rules = AutomationRule.query.filter(
            AutomationRule.is_active == True,
            AutomationRule.cron_expression.isnot(None)
        ).all()
        
        for rule in rules:
            self.schedule_rule(rule)
        
        logger.info(f'Loaded {len(rules)} scheduled rules')
    
    def schedule_rule(self, rule):
        if not rule.cron_expression:
            return False
        
        try:
            trigger = CronTrigger.from_crontab(rule.cron_expression)
            
            job_id = f'rule_{rule.id}'
            
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            self.scheduler.add_job(
                func=self.execute_rule,
                trigger=trigger,
                args=[rule.id],
                id=job_id,
                replace_existing=True,
                name=f'Rule: {rule.name}'
            )
            
            logger.info(f'Scheduled rule {rule.id}: {rule.name}')
            return True
            
        except Exception as e:
            logger.error(f'Error scheduling rule {rule.id}: {e}')
            return False
    
    def execute_rule(self, rule_id):
        with self.app.app_context():
            rule = AutomationRule.query.get(rule_id)
            
            if not rule or not rule.is_active:
                return
            
            event = {
                'type': 'scheduled',
                'rule_id': rule_id,
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': rule.user_id
            }
            
            try:
                result = self.rule_engine.evaluate_rule(rule, event)
                logger.info(f'Executed rule {rule_id}: {result}')
            except Exception as e:
                logger.error(f'Error executing rule {rule_id}: {e}')
    
    def unschedule_rule(self, rule_id):
        job_id = f'rule_{rule_id}'
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f'Unscheduled rule {rule_id}')
            return True
        
        return False
    
    def reload_rule(self, rule_id):
        self.unschedule_rule(rule_id)
        
        with self.app.app_context():
            rule = AutomationRule.query.get(rule_id)
            if rule and rule.is_active and rule.cron_expression:
                return self.schedule_rule(rule)
        
        return False
    
    def get_scheduled_jobs(self):
        jobs = []
        for job in self.scheduler.get_jobs():
            if job.id.startswith('rule_'):
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
        return jobs
    
    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info('Automation scheduler stopped')

scheduler = AutomationScheduler()
