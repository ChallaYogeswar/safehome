from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('mfa_enabled', sa.Boolean(), nullable=True),
    sa.Column('mfa_secret', sa.String(length=32), nullable=True),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=True),
    sa.Column('locked_until', sa.DateTime(), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    op.create_table('cameras',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('location', sa.String(length=100), nullable=True),
    sa.Column('stream_url', sa.String(length=500), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_recording', sa.Boolean(), nullable=True),
    sa.Column('motion_enabled', sa.Boolean(), nullable=True),
    sa.Column('object_detection_enabled', sa.Boolean(), nullable=True),
    sa.Column('face_detection_enabled', sa.Boolean(), nullable=True),
    sa.Column('last_motion', sa.DateTime(), nullable=True),
    sa.Column('last_detection', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cameras_user_id'), 'cameras', ['user_id'], unique=False)
    
    op.create_table('alerts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('alert_type', sa.String(length=50), nullable=False),
    sa.Column('severity', sa.String(length=20), nullable=True),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('source', sa.String(length=100), nullable=True),
    sa.Column('alert_metadata', sa.JSON(), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=True),
    sa.Column('is_acknowledged', sa.Boolean(), nullable=True),
    sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_user_id'), 'alerts', ['user_id'], unique=False)
    op.create_index(op.f('ix_alerts_created_at'), 'alerts', ['created_at'], unique=False)
    
    op.create_table('detections',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('camera_id', sa.Integer(), nullable=False),
    sa.Column('detection_type', sa.String(length=50), nullable=False),
    sa.Column('object_class', sa.String(length=50), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('bbox_x', sa.Integer(), nullable=True),
    sa.Column('bbox_y', sa.Integer(), nullable=True),
    sa.Column('bbox_width', sa.Integer(), nullable=True),
    sa.Column('bbox_height', sa.Integer(), nullable=True),
    sa.Column('image_path', sa.String(length=500), nullable=True),
    sa.Column('detection_metadata', sa.JSON(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detections_camera_id'), 'detections', ['camera_id'], unique=False)
    op.create_index(op.f('ix_detections_timestamp'), 'detections', ['timestamp'], unique=False)
    
    op.create_table('automation_rules',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('trigger_type', sa.String(length=50), nullable=False),
    sa.Column('trigger_config', sa.JSON(), nullable=False),
    sa.Column('conditions', sa.JSON(), nullable=True),
    sa.Column('actions', sa.JSON(), nullable=False),
    sa.Column('cron_expression', sa.String(length=100), nullable=True),
    sa.Column('last_triggered', sa.DateTime(), nullable=True),
    sa.Column('trigger_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_rules_user_id'), 'automation_rules', ['user_id'], unique=False)
    
    op.create_table('security_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('event_description', sa.Text(), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.String(length=500), nullable=True),
    sa.Column('severity', sa.String(length=20), nullable=True),
    sa.Column('log_metadata', sa.JSON(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_logs_event_type'), 'security_logs', ['event_type'], unique=False)
    
    op.create_table('ml_models',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('model_type', sa.String(length=50), nullable=False),
    sa.Column('version', sa.String(length=20), nullable=False),
    sa.Column('file_path', sa.String(length=500), nullable=False),
    sa.Column('accuracy', sa.Float(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('training_data_size', sa.Integer(), nullable=True),
    sa.Column('training_date', sa.DateTime(), nullable=True),
    sa.Column('model_metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('ml_models')
    op.drop_index(op.f('ix_security_logs_event_type'), table_name='security_logs')
    op.drop_table('security_logs')
    op.drop_index(op.f('ix_automation_rules_user_id'), table_name='automation_rules')
    op.drop_table('automation_rules')
    op.drop_index(op.f('ix_detections_timestamp'), table_name='detections')
    op.drop_index(op.f('ix_detections_camera_id'), table_name='detections')
    op.drop_table('detections')
    op.drop_index(op.f('ix_alerts_created_at'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_user_id'), table_name='alerts')
    op.drop_table('alerts')
    op.drop_index(op.f('ix_cameras_user_id'), table_name='cameras')
    op.drop_table('cameras')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
