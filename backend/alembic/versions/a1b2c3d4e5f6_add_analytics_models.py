"""add analytics models

Revision ID: a1b2c3d4e5f6
Revises: f9af749ec562
Create Date: 2026-10-09 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f9af749ec562'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # lms_activity
    op.create_table(
        'lms_activity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('login_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('course_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('videos_watched', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assignments_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('time_spent_hours', sa.Float(), nullable=False, server_default='0'),
        sa.Column('last_active', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id')
    )
    op.create_index(op.f('ix_lms_activity_student_id'), 'lms_activity', ['student_id'], unique=True)

    # skill_assessments
    op.create_table(
        'skill_assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('technical_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('communication_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('teamwork_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('leadership_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('problem_solving_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('aptitude_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('mock_interview_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('assessment_date', sa.Date(), nullable=False),
        sa.Column('assessment_source', sa.String(length=100), nullable=False, server_default='Faculty Evaluation'),
        sa.Column('assessor_faculty_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assessor_faculty_id'], ['faculty.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skill_assessments_student_id'), 'skill_assessments', ['student_id'], unique=False)
    op.create_index(op.f('ix_skill_assessments_assessor_faculty_id'), 'skill_assessments', ['assessor_faculty_id'], unique=False)

    # student_success_scores
    op.create_table(
        'student_success_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('score_category', sa.String(length=50), nullable=False),
        sa.Column('cgpa_component', sa.Float(), nullable=False),
        sa.Column('attendance_component', sa.Float(), nullable=False),
        sa.Column('lms_component', sa.Float(), nullable=False),
        sa.Column('assignment_component', sa.Float(), nullable=False),
        sa.Column('certification_component', sa.Float(), nullable=False),
        sa.Column('placement_component', sa.Float(), nullable=False),
        sa.Column('feedback_component', sa.Float(), nullable=False),
        sa.Column('breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_success_scores_student_id'), 'student_success_scores', ['student_id'], unique=False)
    op.create_index(op.f('ix_student_success_scores_calculated_at'), 'student_success_scores', ['calculated_at'], unique=False)

    # placement_readiness_scores
    op.create_table(
        'placement_readiness_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('coding_score', sa.Float(), nullable=False),
        sa.Column('aptitude_score', sa.Float(), nullable=False),
        sa.Column('communication_score', sa.Float(), nullable=False),
        sa.Column('mock_interview_score', sa.Float(), nullable=False),
        sa.Column('cgpa_score', sa.Float(), nullable=False),
        sa.Column('strengths', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('skill_gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_placement_readiness_scores_student_id'), 'placement_readiness_scores', ['student_id'], unique=False)
    op.create_index(op.f('ix_placement_readiness_scores_calculated_at'), 'placement_readiness_scores', ['calculated_at'], unique=False)

    # academic_risk_predictions
    op.create_table(
        'academic_risk_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('risk_probability', sa.Float(), nullable=False),
        sa.Column('risk_category', sa.String(length=20), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('contributing_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('suggested_interventions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('prediction_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_academic_risk_predictions_student_id'), 'academic_risk_predictions', ['student_id'], unique=False)
    op.create_index(op.f('ix_academic_risk_predictions_prediction_timestamp'), 'academic_risk_predictions', ['prediction_timestamp'], unique=False)

    # placement_risk_predictions
    op.create_table(
        'placement_risk_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('risk_probability', sa.Float(), nullable=False),
        sa.Column('risk_category', sa.String(length=20), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('readiness_score', sa.Float(), nullable=False),
        sa.Column('key_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('prediction_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_placement_risk_predictions_student_id'), 'placement_risk_predictions', ['student_id'], unique=False)
    op.create_index(op.f('ix_placement_risk_predictions_prediction_timestamp'), 'placement_risk_predictions', ['prediction_timestamp'], unique=False)

    # student_segments
    op.create_table(
        'student_segments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('segment_code', sa.String(length=10), nullable=False),
        sa.Column('segment_name', sa.String(length=100), nullable=False),
        sa.Column('assignment_reason', sa.Text(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_segments_student_id'), 'student_segments', ['student_id'], unique=False)
    op.create_index(op.f('ix_student_segments_assigned_at'), 'student_segments', ['assigned_at'], unique=False)

    # interventions
    op.create_table(
        'interventions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('faculty_id', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('urgency', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('action_steps', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('student_notes', sa.Text(), nullable=True),
        sa.Column('faculty_notes', sa.Text(), nullable=True),
        sa.Column('outcome', sa.Text(), nullable=True),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['faculty_id'], ['faculty.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interventions_student_id'), 'interventions', ['student_id'], unique=False)
    op.create_index(op.f('ix_interventions_faculty_id'), 'interventions', ['faculty_id'], unique=False)
    op.create_index(op.f('ix_interventions_created_at'), 'interventions', ['created_at'], unique=False)

    # notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='info'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('link_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)

    # system_settings
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index(op.f('ix_system_settings_key'), 'system_settings', ['key'], unique=True)

    # model_metadata
    op.create_table(
        'model_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('algorithm', sa.String(length=100), nullable=False),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('feature_importances', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('trained_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_metadata_model_name'), 'model_metadata', ['model_name'], unique=False)


def downgrade() -> None:
    op.drop_table('model_metadata')
    op.drop_table('system_settings')
    op.drop_table('notifications')
    op.drop_table('interventions')
    op.drop_table('student_segments')
    op.drop_table('placement_risk_predictions')
    op.drop_table('academic_risk_predictions')
    op.drop_table('placement_readiness_scores')
    op.drop_table('student_success_scores')
    op.drop_table('skill_assessments')
    op.drop_table('lms_activity')
