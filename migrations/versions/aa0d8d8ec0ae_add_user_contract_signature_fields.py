"""add_user_contract_signature_fields_simplified

Revision ID: aa0d8d8ec0ae
Revises: 6e56488a7bd6
Create Date: 2026-03-06 23:07:16.047041

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'aa0d8d8ec0ae'
down_revision = '6e56488a7bd6'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Update Users table (The most critical fix for the reported error)
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('address', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('birth_date', sa.String(length=20), nullable=True))
        # Skip dropping indexes/constraints to avoid MySQL FK issues

    # 2. Update Branches table
    with op.batch_alter_table('branches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_name', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('owner_address', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('owner_birth_date', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('owner_contact', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('owner_seal_image', sa.String(length=255), nullable=True))

    # 3. Update Contracts table
    with op.batch_alter_table('contracts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_address_snapshot', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('user_birth_date_snapshot', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('signature_data', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('signed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('rejection_reason', sa.Text(), nullable=True))

def downgrade():
    with op.batch_alter_table('contracts', schema=None) as batch_op:
        batch_op.drop_column('rejection_reason')
        batch_op.drop_column('signed_at')
        batch_op.drop_column('signature_data')
        batch_op.drop_column('user_birth_date_snapshot')
        batch_op.drop_column('user_address_snapshot')

    with op.batch_alter_table('branches', schema=None) as batch_op:
        batch_op.drop_column('owner_seal_image')
        batch_op.drop_column('owner_contact')
        batch_op.drop_column('owner_birth_date')
        batch_op.drop_column('owner_address')
        batch_op.drop_column('owner_name')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('birth_date')
        batch_op.drop_column('address')
