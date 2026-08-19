"""phase9_disaster_intelligence

Revision ID: 2026_08_19_0003
Revises: 2026_08_19_0002
Create Date: 2026-08-19 18:00:00.000000+00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '2026_08_19_0003'
down_revision: Union[str, None] = '2026_08_19_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'disaster_events' not in existing_tables:
        op.create_table(
            'disaster_events',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('source', sa.String(50), nullable=False, default='mock_provider', index=True),
            sa.Column('external_id', sa.String(100), nullable=True, index=True),
            sa.Column('disaster_type', sa.String(50), nullable=False, index=True),
            sa.Column('severity', sa.Float(), nullable=False, default=5.0, index=True),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('affected_radius_km', sa.Float(), nullable=False, default=15.0),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('status', sa.String(30), nullable=False, default='active', index=True),
            sa.Column('confidence_score', sa.Float(), nullable=False, default=0.85),
            sa.Column('raw_metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'incidents' not in existing_tables:
        op.create_table(
            'incidents',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('event_id', sa.String(36), sa.ForeignKey('disaster_events.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('disaster_type', sa.String(50), nullable=False, index=True),
            sa.Column('severity', sa.Float(), nullable=False, default=5.0, index=True),
            sa.Column('status', sa.String(30), nullable=False, default='DETECTED', index=True),
            sa.Column('escalation_level', sa.String(30), nullable=False, default='LEVEL_1_NORMAL', index=True),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('affected_radius_km', sa.Float(), nullable=False, default=10.0),
            sa.Column('verified_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('resolved_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'incident_timelines' not in existing_tables:
        op.create_table(
            'incident_timelines',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('incident_id', sa.String(36), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('event_type', sa.String(50), nullable=False, index=True),
            sa.Column('message', sa.String(500), nullable=False),
            sa.Column('actor_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
        )

    if 'situation_reports' not in existing_tables:
        op.create_table(
            'situation_reports',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('incident_id', sa.String(36), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('author_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('report_type', sa.String(30), nullable=False, default='field', index=True),
            sa.Column('summary', sa.Text(), nullable=False),
            sa.Column('people_affected', sa.Integer(), nullable=False, default=0),
            sa.Column('people_displaced', sa.Integer(), nullable=False, default=0),
            sa.Column('casualties_reported', sa.Integer(), nullable=False, default=0),
            sa.Column('infrastructure_damage_level', sa.String(20), nullable=False, default='moderate'),
            sa.Column('medical_need_level', sa.String(20), nullable=False, default='moderate'),
            sa.Column('food_need_level', sa.String(20), nullable=False, default='moderate'),
            sa.Column('water_need_level', sa.String(20), nullable=False, default='moderate'),
            sa.Column('shelter_need_level', sa.String(20), nullable=False, default='moderate'),
            sa.Column('communication_status', sa.String(30), nullable=False, default='operational'),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
        )


def downgrade() -> None:
    op.drop_table('situation_reports')
    op.drop_table('incident_timelines')
    op.drop_table('incidents')
    op.drop_table('disaster_events')
