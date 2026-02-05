from app.models import db
from app.services.alert_service import AlertService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RuleEngine:
    
    def __init__(self):
        self.alert_service = AlertService()
    
    def evaluate_rule(self, rule, event):
        if not rule.is_active:
            return {'matched': False, 'reason': 'Rule is inactive'}
        
        trigger_matched = self._check_trigger(rule, event)
        if not trigger_matched:
            return {'matched': False, 'reason': 'Trigger not matched'}
        
        conditions_met = self._check_conditions(rule, event)
        if not conditions_met:
            return {'matched': False, 'reason': 'Conditions not met'}
        
        actions_executed = self._execute_actions(rule, event)
        
        rule.last_triggered = datetime.utcnow()
        rule.trigger_count += 1
        db.session.commit()
        
        return {
            'matched': True,
            'actions_executed': actions_executed,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _check_trigger(self, rule, event):
        if rule.trigger_type == 'sensor':
            return event.get('type') in ['motion_detected', 'object_detected', 'face_detected']
        
        elif rule.trigger_type == 'time':
            return True
        
        elif rule.trigger_type == 'user_action':
            return event.get('type') in ['login', 'logout']
        
        elif rule.trigger_type == 'anomaly':
            return event.get('type') == 'anomaly_detected'
        
        return False
    
    def _check_conditions(self, rule, event):
        if not rule.conditions:
            return True
        
        for condition in rule.conditions:
            field = condition.get('field')
            operator = condition.get('op')
            value = condition.get('value')
            
            event_value = event.get(field)
            
            if operator == 'eq':
                if event_value != value:
                    return False
            
            elif operator == 'neq':
                if event_value == value:
                    return False
            
            elif operator == 'gt':
                if not (event_value and event_value > value):
                    return False
            
            elif operator == 'lt':
                if not (event_value and event_value < value):
                    return False
            
            elif operator == 'contains':
                if not (event_value and value in str(event_value)):
                    return False
            
            elif operator == 'between':
                if not (event_value and value[0] <= event_value <= value[1]):
                    return False
        
        return True
    
    def _execute_actions(self, rule, event):
        executed = []
        
        for action in rule.actions:
            action_type = action.get('type')
            
            try:
                if action_type == 'send_alert':
                    self._action_send_alert(rule, event, action)
                    executed.append('send_alert')
                
                elif action_type == 'notify_user':
                    self._action_notify_user(rule, event, action)
                    executed.append('notify_user')
                
                elif action_type == 'log_event':
                    self._action_log_event(rule, event, action)
                    executed.append('log_event')
                
            except Exception as e:
                logger.error(f"Error executing action {action_type}: {e}")
        
        return executed
    
    def _action_send_alert(self, rule, event, action):
        severity = action.get('severity', 'medium')
        
        self.alert_service.create_alert(
            user_id=rule.user_id,
            alert_type='automation_rule',
            title=f"Rule Triggered: {rule.name}",
            message=f"Automation rule '{rule.name}' was triggered",
            severity=severity,
            source='automation',
            metadata={
                'rule_id': rule.id,
                'event': event
            }
        )
    
    def _action_notify_user(self, rule, event, action):
        message = action.get('message', f"Rule {rule.name} triggered")
        
        self.alert_service.create_alert(
            user_id=rule.user_id,
            alert_type='notification',
            title='Automation Notification',
            message=message,
            severity='low',
            source='automation'
        )
    
    def _action_log_event(self, rule, event, action):
        logger.info(f"Rule {rule.id} ({rule.name}) triggered with event: {event}")
    
    def evaluate_all_rules_for_event(self, event):
        from app.models import AutomationRule
        
        user_id = event.get('user_id')
        if not user_id:
            return
        
        rules = AutomationRule.query.filter_by(user_id=user_id, is_active=True).all()
        
        for rule in rules:
            try:
                self.evaluate_rule(rule, event)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}")
