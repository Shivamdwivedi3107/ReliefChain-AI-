"""initial_schema

Revision ID: 2026_08_19_0001
Revises: 
Create Date: 2026-08-19 12:00:00.000000+00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '2026_08_19_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use inspector or safe conditional table creation for cross-engine (SQLite & PostgreSQL) compatibility
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'organizations' not in existing_tables:
        op.create_table(
            'organizations',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('name', sa.String(150), unique=True, nullable=False, index=True),
            sa.Column('registration_number', sa.String(100), unique=True, nullable=False),
            sa.Column('organization_type', sa.String(50), nullable=False),
            sa.Column('contact_email', sa.String(120), unique=True, nullable=False),
            sa.Column('contact_phone', sa.String(30), nullable=False),
            sa.Column('address', sa.Text(), nullable=True),
            sa.Column('wallet_address', sa.String(64), nullable=True),
            sa.Column('verification_status', sa.String(30), nullable=False, default='verified', index=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('email', sa.String(120), unique=True, nullable=False, index=True),
            sa.Column('full_name', sa.String(120), nullable=False),
            sa.Column('hashed_password', sa.String(255), nullable=False),
            sa.Column('role', sa.String(30), nullable=False, index=True),
            sa.Column('phone_number', sa.String(30), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
            sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
            sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    if 'disasters' not in existing_tables:
        op.create_table(
            'disasters',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('title', sa.String(150), nullable=False, index=True),
            sa.Column('disaster_type', sa.String(50), nullable=False, index=True),
            sa.Column('severity', sa.String(30), nullable=False, index=True),
            sa.Column('status', sa.String(30), nullable=False, index=True),
            sa.Column('location_name', sa.String(200), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('radius_km', sa.Float(), nullable=False, default=10.0),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    if 'resources' not in existing_tables:
        op.create_table(
            'resources',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('name', sa.String(120), unique=True, nullable=False),
            sa.Column('category', sa.String(50), nullable=False, index=True),
            sa.Column('unit', sa.String(30), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    if 'resource_inventories' not in existing_tables:
        op.create_table(
            'resource_inventories',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('resource_id', sa.String(36), sa.ForeignKey('resources.id', ondelete='CASCADE'), nullable=False),
            sa.Column('total_quantity', sa.Float(), nullable=False, default=0.0),
            sa.Column('available_quantity', sa.Float(), nullable=False, default=0.0),
            sa.Column('reserved_quantity', sa.Float(), nullable=False, default=0.0),
            sa.Column('warehouse_location', sa.String(200), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.UniqueConstraint('organization_id', 'resource_id', name='uq_org_resource_inventory'),
        )

    if 'relief_requests' not in existing_tables:
        op.create_table(
            'relief_requests',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('citizen_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('disaster_id', sa.String(36), sa.ForeignKey('disasters.id', ondelete='SET NULL'), nullable=True),
            sa.Column('disaster_type', sa.String(50), nullable=False, index=True),
            sa.Column('location_name', sa.String(200), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('affected_people', sa.Integer(), nullable=False, default=1),
            sa.Column('required_resources', sa.JSON(), nullable=False),
            sa.Column('urgency_description', sa.Text(), nullable=True),
            sa.Column('image_reference', sa.String(255), nullable=True),
            sa.Column('priority', sa.String(30), nullable=False, default='medium', index=True),
            sa.Column('status', sa.String(30), nullable=False, default='pending', index=True),
            sa.Column('assigned_organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
            sa.Column('assigned_volunteer_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('ai_predicted_priority', sa.String(30), nullable=True),
            sa.Column('ai_confidence', sa.Float(), nullable=True),
            sa.Column('ai_factors', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    if 'donations' not in existing_tables:
        op.create_table(
            'donations',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('donor_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('donor_name', sa.String(120), nullable=False),
            sa.Column('donor_email', sa.String(120), nullable=True),
            sa.Column('donation_type', sa.String(30), nullable=False),
            sa.Column('currency', sa.String(10), nullable=True, default='USD'),
            sa.Column('amount', sa.Float(), nullable=True),
            sa.Column('resource_id', sa.String(36), sa.ForeignKey('resources.id', ondelete='SET NULL'), nullable=True),
            sa.Column('quantity', sa.Float(), nullable=True),
            sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False),
            sa.Column('status', sa.String(30), nullable=False, default='completed'),
            sa.Column('transaction_reference', sa.String(100), nullable=True),
            sa.Column('record_hash', sa.String(64), nullable=True),
            sa.Column('blockchain_tx_hash', sa.String(66), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    if 'distributions' not in existing_tables:
        op.create_table(
            'distributions',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('relief_request_id', sa.String(36), sa.ForeignKey('relief_requests.id', ondelete='CASCADE'), nullable=False),
            sa.Column('resource_id', sa.String(36), sa.ForeignKey('resources.id', ondelete='RESTRICT'), nullable=False),
            sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False),
            sa.Column('volunteer_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('recipient_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('quantity', sa.Float(), nullable=False),
            sa.Column('status', sa.String(30), nullable=False, default='dispatched'),
            sa.Column('dispatch_location', sa.String(200), nullable=True),
            sa.Column('delivery_latitude', sa.Float(), nullable=True),
            sa.Column('delivery_longitude', sa.Float(), nullable=True),
            sa.Column('record_hash', sa.String(64), nullable=True),
            sa.Column('blockchain_tx_hash', sa.String(66), nullable=True),
            sa.Column('qr_token', sa.String(128), unique=True, nullable=True),
            sa.Column('dispatched_at', sa.DateTime(), nullable=True),
            sa.Column('delivered_at', sa.DateTime(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    if 'blockchain_transactions' not in existing_tables:
        op.create_table(
            'blockchain_transactions',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('event_type', sa.String(50), nullable=False, index=True),
            sa.Column('reference_id', sa.String(36), nullable=False, index=True),
            sa.Column('record_hash', sa.String(64), nullable=False, index=True),
            sa.Column('previous_hash', sa.String(64), nullable=True),
            sa.Column('tx_hash', sa.String(66), unique=True, nullable=True),
            sa.Column('block_number', sa.Integer(), nullable=True),
            sa.Column('from_address', sa.String(42), nullable=True),
            sa.Column('contract_address', sa.String(42), nullable=True),
            sa.Column('status', sa.String(30), nullable=False, default='confirmed'),
            sa.Column('raw_receipt', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    if 'qr_verifications' not in existing_tables:
        op.create_table(
            'qr_verifications',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('distribution_id', sa.String(36), sa.ForeignKey('distributions.id', ondelete='CASCADE'), nullable=False),
            sa.Column('verification_token', sa.String(128), unique=True, nullable=False),
            sa.Column('qr_code_data', sa.Text(), nullable=True),
            sa.Column('status', sa.String(30), nullable=False, default='active'),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('verified_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('verification_lat', sa.Float(), nullable=True),
            sa.Column('verification_lng', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    if 'prediction_histories' not in existing_tables:
        op.create_table(
            'prediction_histories',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('request_id', sa.String(36), sa.ForeignKey('relief_requests.id', ondelete='SET NULL'), nullable=True),
            sa.Column('disaster_type', sa.String(50), nullable=False),
            sa.Column('affected_people', sa.Integer(), nullable=False),
            sa.Column('location_risk_score', sa.Float(), nullable=False),
            sa.Column('medical_needed', sa.Integer(), nullable=False),
            sa.Column('food_needed', sa.Integer(), nullable=False),
            sa.Column('water_needed', sa.Integer(), nullable=False),
            sa.Column('vulnerable_population', sa.Integer(), nullable=False),
            sa.Column('predicted_priority', sa.String(30), nullable=False),
            sa.Column('confidence_score', sa.Float(), nullable=False),
            sa.Column('contributing_factors', sa.JSON(), nullable=True),
            sa.Column('model_version', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    if 'notifications' not in existing_tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('title', sa.String(150), nullable=False),
            sa.Column('message', sa.String(500), nullable=False),
            sa.Column('notification_type', sa.String(50), nullable=False, index=True),
            sa.Column('severity', sa.String(30), nullable=False, default='info'),
            sa.Column('is_read', sa.Boolean(), nullable=False, default=False, index=True),
            sa.Column('reference_id', sa.String(36), nullable=True),
            sa.Column('reference_type', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    if 'mission_status_histories' not in existing_tables:
        op.create_table(
            'mission_status_histories',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('relief_request_id', sa.String(36), sa.ForeignKey('relief_requests.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('previous_status', sa.String(30), nullable=True),
            sa.Column('new_status', sa.String(30), nullable=False, index=True),
            sa.Column('changed_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('optional_note', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    if 'audit_logs' not in existing_tables:
        op.create_table(
            'audit_logs',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('action', sa.String(100), nullable=False, index=True),
            sa.Column('entity_type', sa.String(50), nullable=False, index=True),
            sa.Column('entity_id', sa.String(36), nullable=True, index=True),
            sa.Column('details_json', sa.JSON(), nullable=True),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('mission_status_histories')
    op.drop_table('notifications')
    op.drop_table('prediction_histories')
    op.drop_table('qr_verifications')
    op.drop_table('blockchain_transactions')
    op.drop_table('distributions')
    op.drop_table('donations')
    op.drop_table('relief_requests')
    op.drop_table('resource_inventories')
    op.drop_table('resources')
    op.drop_table('disasters')
    op.drop_table('users')
    op.drop_table('organizations')
