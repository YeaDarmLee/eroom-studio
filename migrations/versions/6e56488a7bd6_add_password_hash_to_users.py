"""Add password_hash to users

Revision ID: 6e56488a7bd6
Revises: 120af649950d
Create Date: 2025-11-30 17:24:02.762433

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6e56488a7bd6'
down_revision = '120af649950d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('users', 'password_hash')
