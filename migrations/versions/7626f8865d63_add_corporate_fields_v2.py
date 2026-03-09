"""add_corporate_fields_v2

Revision ID: 7626f8865d63
Revises: aa0d8d8ec0ae
Create Date: 2026-03-06 23:51:17.202349

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '7626f8865d63'
down_revision = 'aa0d8d8ec0ae'
branch_labels = None
depends_on = None


def upgrade():
    # Only add the columns that are actually missing
    with op.batch_alter_table('branches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_user_id', mysql.INTEGER(unsigned=True), nullable=True))
        batch_op.add_column(sa.Column('is_corporate', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('registration_number', sa.String(length=50), nullable=True))
        batch_op.create_foreign_key('fk_branches_owner_user_id', 'users', ['owner_user_id'], ['id'])
        # Drop old columns if they exist and are not in the model
        batch_op.drop_column('contact_info')
        batch_op.drop_column('transport_info')

def downgrade():
    with op.batch_alter_table('branches', schema=None) as batch_op:
        batch_op.drop_constraint('fk_branches_owner_user_id', type_='foreignkey')
        batch_op.drop_column('registration_number')
        batch_op.drop_column('is_corporate')
        batch_op.drop_column('owner_user_id')
        batch_op.add_column(sa.Column('transport_info', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('contact_info', sa.String(length=255), nullable=True))
