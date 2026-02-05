from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, AutomationRule
from app.services.rule_engine import RuleEngine
from datetime import datetime

bp = Blueprint('automation', __name__, url_prefix='/automation')
rule_engine = RuleEngine()

@bp.route('/')
@login_required
def index():
    rules = AutomationRule.query.filter_by(user_id=current_user.id)\
        .order_by(AutomationRule.created_at.desc())\
        .all()
    
    return render_template('automation.html', rules=rules)

@bp.route('/create', methods=['POST'])
@login_required
def create_rule():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    description = data.get('description', '')
    trigger_type = data.get('trigger_type')
    trigger_config = data.get('trigger_config', {})
    conditions = data.get('conditions', [])
    actions = data.get('actions', [])
    cron_expression = data.get('cron_expression')
    
    if not name or not trigger_type or not actions:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    rule = AutomationRule(
        user_id=current_user.id,
        name=name,
        description=description,
        trigger_type=trigger_type,
        trigger_config=trigger_config,
        conditions=conditions,
        actions=actions,
        cron_expression=cron_expression,
        is_active=True
    )
    
    db.session.add(rule)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'rule': {
            'id': rule.id,
            'name': rule.name,
            'trigger_type': rule.trigger_type,
            'is_active': rule.is_active
        }
    })

@bp.route('/<int:rule_id>', methods=['GET'])
@login_required
def get_rule(rule_id):
    rule = AutomationRule.query.filter_by(id=rule_id, user_id=current_user.id).first()
    
    if not rule:
        return jsonify({'success': False, 'error': 'Rule not found'}), 404
    
    return jsonify({
        'success': True,
        'rule': {
            'id': rule.id,
            'name': rule.name,
            'description': rule.description,
            'trigger_type': rule.trigger_type,
            'trigger_config': rule.trigger_config,
            'conditions': rule.conditions,
            'actions': rule.actions,
            'cron_expression': rule.cron_expression,
            'is_active': rule.is_active,
            'last_triggered': rule.last_triggered.isoformat() if rule.last_triggered else None,
            'trigger_count': rule.trigger_count
        }
    })

@bp.route('/<int:rule_id>/update', methods=['PUT'])
@login_required
def update_rule(rule_id):
    rule = AutomationRule.query.filter_by(id=rule_id, user_id=current_user.id).first()
    
    if not rule:
        return jsonify({'success': False, 'error': 'Rule not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        rule.name = data['name']
    if 'description' in data:
        rule.description = data['description']
    if 'trigger_type' in data:
        rule.trigger_type = data['trigger_type']
    if 'trigger_config' in data:
        rule.trigger_config = data['trigger_config']
    if 'conditions' in data:
        rule.conditions = data['conditions']
    if 'actions' in data:
        rule.actions = data['actions']
    if 'cron_expression' in data:
        rule.cron_expression = data['cron_expression']
    if 'is_active' in data:
        rule.is_active = data['is_active']
    
    rule.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/<int:rule_id>/delete', methods=['DELETE'])
@login_required
def delete_rule(rule_id):
    rule = AutomationRule.query.filter_by(id=rule_id, user_id=current_user.id).first()
    
    if not rule:
        return jsonify({'success': False, 'error': 'Rule not found'}), 404
    
    db.session.delete(rule)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/<int:rule_id>/toggle', methods=['POST'])
@login_required
def toggle_rule(rule_id):
    rule = AutomationRule.query.filter_by(id=rule_id, user_id=current_user.id).first()
    
    if not rule:
        return jsonify({'success': False, 'error': 'Rule not found'}), 404
    
    rule.is_active = not rule.is_active
    db.session.commit()
    
    return jsonify({'success': True, 'is_active': rule.is_active})

@bp.route('/<int:rule_id>/test', methods=['POST'])
@login_required
def test_rule(rule_id):
    rule = AutomationRule.query.filter_by(id=rule_id, user_id=current_user.id).first()
    
    if not rule:
        return jsonify({'success': False, 'error': 'Rule not found'}), 404
    
    test_event = request.get_json().get('event', {})
    
    result = rule_engine.evaluate_rule(rule, test_event)
    
    return jsonify({
        'success': True,
        'matched': result['matched'],
        'actions_executed': result.get('actions_executed', []),
        'errors': result.get('errors', [])
    })
