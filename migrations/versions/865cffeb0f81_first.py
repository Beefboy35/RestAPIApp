"""first

Revision ID: 865cffeb0f81
Revises: 
Create Date: 2025-02-13 20:50:05.252419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text

# revision identifiers, used by Alembic.
revision: str = '865cffeb0f81'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Создание таблицы buildings
    op.create_table(
        'buildings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
    )

    # Создание таблицы organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('phone_numbers', Text, nullable=True),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('building_id', sa.Integer(), sa.ForeignKey('buildings.id')),
    )

    # Создание таблицы activities
    op.create_table(
        'activities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('activities.id')),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id')),
    )

def downgrade():
    # Удаление таблицы activities
    op.drop_table('activities')

    # Удаление таблицы organizations
    op.drop_table('organizations')

    # Удаление таблицы buildings
    op.drop_table('buildings')