"""phase8_ai_intelligence

Revision ID: 2026_08_19_0002
Revises: 2026_08_19_0001
Create Date: 2026-08-19 16:00:00.000000+00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '2026_08_19_0002'
down_revision: Union[str, None] = '2026_08_19_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'ai_model_registry' not in existing_tables:
        op.create_table(
            'ai_model_registry',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('model_name', sa.String(100), unique=True, nullable=False, index=True),
            sa.Column('model_version', sa.String(50), nullable=False, index=True),
            sa.Column('model_type', sa.String(50), nullable=False),
            sa.Column('accuracy', sa.Float(), nullable=False),
            sa.Column('f1_score', sa.Float(), nullable=True),
            sa.Column('dataset_version', sa.String(50), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=True, index=True),
            sa.Column('artifact_path', sa.String(255), nullable=True),
            sa.Column('checksum_sha256', sa.String(64), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'disaster_risk_predictions' not in existing_tables:
        op.create_table(
            'disaster_risk_predictions',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('disaster_type', sa.String(50), nullable=False, index=True),
            sa.Column('location_name', sa.String(200), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('risk_score', sa.Float(), nullable=False, index=True),
            sa.Column('risk_level', sa.String(30), nullable=False, index=True),
            sa.Column('confidence', sa.Float(), nullable=False),
            sa.Column('input_parameters', sa.JSON(), nullable=False),
            sa.Column('risk_factors', sa.JSON(), nullable=False),
            sa.Column('recommendations', sa.JSON(), nullable=False),
            sa.Column('model_version', sa.String(50), nullable=False),
            sa.Column('created_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'resource_forecasts' not in existing_tables:
        op.create_table(
            'resource_forecasts',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('disaster_type', sa.String(50), nullable=False, index=True),
            sa.Column('severity', sa.Float(), nullable=False),
            sa.Column('population_affected', sa.Integer(), nullable=False),
            sa.Column('forecast_period_hours', sa.Integer(), nullable=False),
            sa.Column('predicted_demand', sa.JSON(), nullable=False),
            sa.Column('inventory_gap', sa.JSON(), nullable=False),
            sa.Column('recommendations', sa.JSON(), nullable=False),
            sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('created_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'disaster_simulations' not in existing_tables:
        op.create_table(
            'disaster_simulations',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('scenario_title', sa.String(150), nullable=False, index=True),
            sa.Column('disaster_type', sa.String(50), nullable=False, index=True),
            sa.Column('severity', sa.Float(), nullable=False),
            sa.Column('population_affected', sa.Integer(), nullable=False),
            sa.Column('duration_hours', sa.Integer(), nullable=False),
            sa.Column('location_name', sa.String(200), nullable=False),
            sa.Column('simulation_results', sa.JSON(), nullable=False),
            sa.Column('created_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    op.drop_table('disaster_simulations')
    op.drop_table('resource_forecasts')
    op.drop_table('disaster_risk_predictions')
    op.drop_table('ai_model_registry')
