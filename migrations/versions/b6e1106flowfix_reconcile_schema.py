"""Expand the legacy schema to the 2026-11-06 application schema.

No tables/columns are removed. Apply only after schema review and backup.
Downgrade retains the expanded schema so application rollback preserves data.
"""
from alembic import op
import sqlalchemy as sa
revision = 'b6e1106flowfix'
down_revision = '7626f8865d63'
branch_labels = None
depends_on = None

def target_schema():
    metadata = sa.MetaData()
    sa.Table('coupons', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('code', sa.String(50), primary_key=False, nullable=False),
        sa.Column('discount_type', sa.String(20), primary_key=False, nullable=False),
        sa.Column('discount_value', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('discount_cycle', sa.String(20), primary_key=False, nullable=True),
        sa.Column('stack_policy', sa.String(30), primary_key=False, nullable=True),
        sa.Column('valid_from', sa.Date(), primary_key=False, nullable=False),
        sa.Column('valid_until', sa.Date(), primary_key=False, nullable=False),
        sa.Column('min_months', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('usage_limit', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('used_count', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('is_active', sa.Boolean(), primary_key=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.UniqueConstraint('code', name='uq_coupons_code'),
    )
    sa.Table('sms_templates', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('type', sa.String(50), primary_key=False, nullable=False),
        sa.Column('title', sa.String(100), primary_key=False, nullable=True),
        sa.Column('content', sa.Text(), primary_key=False, nullable=False),
        sa.Column('is_active', sa.Boolean(), primary_key=False, nullable=True),
        sa.Column('schedule_offset', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('updated_by_admin_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('updated_reason', sa.String(255), primary_key=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.Column('updated_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.UniqueConstraint('type', name='uq_sms_templates_type'),
    )
    sa.Table('terms_documents', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('version', sa.String(50), primary_key=False, nullable=False),
        sa.Column('content', sa.Text(), primary_key=False, nullable=False),
        sa.Column('content_hash', sa.String(64), primary_key=False, nullable=False),
        sa.Column('published_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.Column('is_active', sa.Boolean(), primary_key=False, nullable=True),
        sa.UniqueConstraint('version', name='uq_terms_documents_version'),
    )
    sa.Table('users', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('kakao_id', sa.String(64), primary_key=False, nullable=True),
        sa.Column('email', sa.String(120), primary_key=False, nullable=True),
        sa.Column('phone', sa.String(20), primary_key=False, nullable=True),
        sa.Column('name', sa.String(64), primary_key=False, nullable=True),
        sa.Column('address', sa.String(255), primary_key=False, nullable=True),
        sa.Column('birth_date', sa.String(20), primary_key=False, nullable=True),
        sa.Column('registration_number', sa.String(20), primary_key=False, nullable=True),
        sa.Column('role', sa.String(20), primary_key=False, nullable=True),
        sa.Column('onboarding_status', sa.String(20), primary_key=False, nullable=True),
        sa.Column('password_hash', sa.String(255), primary_key=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.UniqueConstraint('kakao_id', name='uq_users_kakao_id'),
        sa.UniqueConstraint('phone', name='uq_users_phone'),
    )
    sa.Table('branches', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(100), primary_key=False, nullable=False),
        sa.Column('description', sa.Text(), primary_key=False, nullable=True),
        sa.Column('address', sa.String(200), primary_key=False, nullable=True),
        sa.Column('map_info', sa.Text(), primary_key=False, nullable=True),
        sa.Column('facilities', sa.Text(), primary_key=False, nullable=True),
        sa.Column('image_url', sa.String(255), primary_key=False, nullable=True),
        sa.Column('operating_hours', sa.String(100), primary_key=False, nullable=True),
        sa.Column('contact', sa.String(50), primary_key=False, nullable=True),
        sa.Column('traffic_info', sa.Text(), primary_key=False, nullable=True),
        sa.Column('parking_info', sa.Text(), primary_key=False, nullable=True),
        sa.Column('owner_user_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('is_corporate', sa.Boolean(), primary_key=False, nullable=True),
        sa.Column('registration_number', sa.String(50), primary_key=False, nullable=True),
        sa.Column('owner_name', sa.String(64), primary_key=False, nullable=True),
        sa.Column('owner_address', sa.String(255), primary_key=False, nullable=True),
        sa.Column('owner_birth_date', sa.String(20), primary_key=False, nullable=True),
        sa.Column('owner_contact', sa.String(50), primary_key=False, nullable=True),
        sa.Column('owner_seal_image', sa.String(255), primary_key=False, nullable=True),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], name='fk_branches_owner_user_id'),
    )
    sa.Table('tenant_room_link_requests', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('branch_name', sa.String(100), primary_key=False, nullable=True),
        sa.Column('room_name', sa.String(50), primary_key=False, nullable=True),
        sa.Column('memo', sa.Text(), primary_key=False, nullable=True),
        sa.Column('status', sa.String(20), primary_key=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_tenant_room_link_requests_user_id'),
    )
    sa.Table('branch_floors', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('branch_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('floor', sa.String(20), primary_key=False, nullable=False),
        sa.Column('floor_plan_image', sa.String(255), primary_key=False, nullable=True),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_branch_floors_branch_id'),
        sa.UniqueConstraint('branch_id', 'floor', name='unique_branch_floor'),
    )
    sa.Table('branch_images', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('branch_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('image_url', sa.String(255), primary_key=False, nullable=False),
        sa.Column('order_index', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_branch_images_branch_id'),
    )
    sa.Table('rooms', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('branch_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('floor', sa.String(20), primary_key=False, nullable=True),
        sa.Column('name', sa.String(50), primary_key=False, nullable=False),
        sa.Column('description', sa.Text(), primary_key=False, nullable=True),
        sa.Column('room_type', sa.String(20), primary_key=False, nullable=True),
        sa.Column('price', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('deposit', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('area', sa.Float(), primary_key=False, nullable=True),
        sa.Column('status', sa.String(20), primary_key=False, nullable=True),
        sa.Column('position_x', sa.Float(), primary_key=False, nullable=True),
        sa.Column('position_y', sa.Float(), primary_key=False, nullable=True),
        sa.Column('width', sa.Float(), primary_key=False, nullable=True),
        sa.Column('height', sa.Float(), primary_key=False, nullable=True),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_rooms_branch_id'),
    )
    sa.Table('contracts', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('room_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('temp_user_name', sa.String(64), primary_key=False, nullable=True),
        sa.Column('temp_user_phone', sa.String(20), primary_key=False, nullable=True),
        sa.Column('temp_user_email', sa.String(120), primary_key=False, nullable=True),
        sa.Column('start_date', sa.Date(), primary_key=False, nullable=False),
        sa.Column('end_date', sa.Date(), primary_key=False, nullable=False),
        sa.Column('start_time', sa.String(10), primary_key=False, nullable=True),
        sa.Column('end_time', sa.String(10), primary_key=False, nullable=True),
        sa.Column('months', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('price', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('deposit', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('payment_method', sa.String(20), primary_key=False, nullable=True),
        sa.Column('payment_day', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('paid_months', sa.JSON(), primary_key=False, nullable=True),
        sa.Column('coupon_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('discount_details', sa.Text(), primary_key=False, nullable=True),
        sa.Column('is_indefinite', sa.Boolean(), primary_key=False, nullable=True),
        sa.Column('status', sa.String(20), primary_key=False, nullable=True),
        sa.Column('auto_extend_status', sa.String(20), primary_key=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.Column('terms_document_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('terms_version', sa.String(50), primary_key=False, nullable=True),
        sa.Column('terms_snapshot_hash', sa.String(64), primary_key=False, nullable=True),
        sa.Column('consented_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.Column('consent_ip', sa.String(45), primary_key=False, nullable=True),
        sa.Column('consent_user_agent', sa.Text(), primary_key=False, nullable=True),
        sa.Column('consent_method', sa.String(50), primary_key=False, nullable=True),
        sa.Column('tax_invoice_requested', sa.Boolean(), primary_key=False, nullable=True),
        sa.Column('pricing_snapshot', sa.JSON(), primary_key=False, nullable=True),
        sa.Column('penalty_formula_version', sa.String(50), primary_key=False, nullable=True),
        sa.Column('penalty_rule_text', sa.Text(), primary_key=False, nullable=True),
        sa.Column('contract_email_snapshot', sa.String(120), primary_key=False, nullable=True),
        sa.Column('contract_notice_sent_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.Column('notice_email_to', sa.String(120), primary_key=False, nullable=True),
        sa.Column('notice_email_attempts', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('notice_last_error', sa.Text(), primary_key=False, nullable=True),
        sa.Column('contract_pdf_hash', sa.String(64), primary_key=False, nullable=True),
        sa.Column('user_address_snapshot', sa.String(255), primary_key=False, nullable=True),
        sa.Column('user_birth_date_snapshot', sa.String(20), primary_key=False, nullable=True),
        sa.Column('user_registration_number_snapshot', sa.String(20), primary_key=False, nullable=True),
        sa.Column('signature_data', sa.Text(), primary_key=False, nullable=True),
        sa.Column('signed_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.Column('rejection_reason', sa.Text(), primary_key=False, nullable=True),
        sa.Column('termination_requested_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.Column('termination_effective_date', sa.Date(), primary_key=False, nullable=True),
        sa.Column('remaining_months_at_termination', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('penalty_amount_snapshot', sa.JSON(), primary_key=False, nullable=True),
        sa.Column('termination_confirmation_checked', sa.Boolean(), primary_key=False, nullable=True),
        sa.Column('termination_confirmation_text_snapshot', sa.Text(), primary_key=False, nullable=True),
        sa.ForeignKeyConstraint(['coupon_id'], ['coupons.id'], name='fk_contracts_coupon_id'),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], name='fk_contracts_room_id'),
        sa.ForeignKeyConstraint(['terms_document_id'], ['terms_documents.id'], name='fk_contracts_terms_document_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_contracts_user_id'),
    )
    sa.Table('room_images', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('room_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('image_url', sa.String(255), primary_key=False, nullable=False),
        sa.Column('order_index', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], name='fk_room_images_room_id'),
    )
    sa.Table('contract_status_history', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('contract_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('old_status', sa.String(20), primary_key=False, nullable=True),
        sa.Column('new_status', sa.String(20), primary_key=False, nullable=False),
        sa.Column('actor_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('actor_type', sa.String(10), primary_key=False, nullable=True),
        sa.Column('actor_ip', sa.String(45), primary_key=False, nullable=True),
        sa.Column('actor_user_agent', sa.Text(), primary_key=False, nullable=True),
        sa.Column('source', sa.String(20), primary_key=False, nullable=True),
        sa.Column('changed_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.Column('reason', sa.Text(), primary_key=False, nullable=True),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], name='fk_contract_status_history_contract_id'),
    )
    sa.Table('custom_discounts', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('contract_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('target_month', sa.String(7), primary_key=False, nullable=False),
        sa.Column('amount', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('reason', sa.String(255), primary_key=False, nullable=True),
        sa.Column('admin_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.Column('updated_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], name='fk_custom_discounts_admin_id'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], name='fk_custom_discounts_contract_id'),
        sa.UniqueConstraint('contract_id', 'target_month', name='uix_custom_discount_contract_month'),
    )
    sa.Table('requests', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('contract_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('type', sa.String(20), primary_key=False, nullable=False),
        sa.Column('status', sa.String(20), primary_key=False, nullable=True),
        sa.Column('details', sa.Text(), primary_key=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.Column('updated_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], name='fk_requests_contract_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_requests_user_id'),
    )
    sa.Table('sms_logs', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('contract_id', sa.Integer(), primary_key=False, nullable=True),
        sa.Column('type', sa.String(50), primary_key=False, nullable=False),
        sa.Column('dedup_key', sa.String(100), primary_key=False, nullable=False),
        sa.Column('related_date', sa.Date(), primary_key=False, nullable=True),
        sa.Column('content_snapshot', sa.Text(), primary_key=False, nullable=False),
        sa.Column('context_snapshot', sa.JSON(), primary_key=False, nullable=True),
        sa.Column('status', sa.String(20), primary_key=False, nullable=False),
        sa.Column('provider_info', sa.String(50), primary_key=False, nullable=True),
        sa.Column('provider_message_id', sa.String(100), primary_key=False, nullable=True),
        sa.Column('error_message', sa.Text(), primary_key=False, nullable=True),
        sa.Column('sent_at', sa.DateTime(), primary_key=False, nullable=True),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], name='fk_sms_logs_contract_id'),
        sa.UniqueConstraint('dedup_key', name='uq_sms_logs_dedup_key'),
    )
    return metadata

def upgrade():
    bind = op.get_bind()
    metadata = target_schema()
    existing_tables = set(sa.inspect(bind).get_table_names())
    for table in metadata.sorted_tables:
        if table.name not in existing_tables:
            table.create(bind)
            continue
        columns = {c['name']: c for c in sa.inspect(bind).get_columns(table.name)}
        for column in table.columns:
            if column.name not in columns:
                # Add nullable fields first; populated legacy rows must remain valid.
                op.add_column(table.name, sa.Column(column.name, column.type, nullable=True))
        if table.name == 'contracts' and not columns['user_id']['nullable']:
            with op.batch_alter_table('contracts') as batch:
                batch.alter_column('user_id', existing_type=sa.Integer(), nullable=True)

    # Preserve total_price for compatibility; only fill new, empty price values.
    columns = {c['name'] for c in sa.inspect(bind).get_columns('contracts')}
    if 'total_price' in columns:
        op.execute(sa.text('UPDATE contracts SET price = total_price WHERE price IS NULL AND total_price IS NOT NULL'))
    op.execute(sa.text("UPDATE contracts SET auto_extend_status = 'none' WHERE auto_extend_status IS NULL"))
    op.execute(sa.text('UPDATE contracts SET is_indefinite = 0 WHERE is_indefinite IS NULL'))

    for table in metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        inspector = sa.inspect(bind)
        existing_fk = {tuple(fk['constrained_columns']) for fk in inspector.get_foreign_keys(table.name)}
        existing_unique = {tuple(c['column_names']) for c in inspector.get_unique_constraints(table.name)}
        with op.batch_alter_table(table.name) as batch:
            for fk in table.foreign_key_constraints:
                if tuple(fk.column_keys) not in existing_fk:
                    elements = list(fk.elements)
                    batch.create_foreign_key(fk.name, elements[0].column.table.name,
                                             list(fk.column_keys), [e.column.name for e in elements])
            for constraint in table.constraints:
                if isinstance(constraint, sa.UniqueConstraint) and tuple(constraint.columns.keys()) not in existing_unique:
                    batch.create_unique_constraint(constraint.name, list(constraint.columns.keys()))


def downgrade():
    # Expansion is intentionally retained for data-preserving application rollback.
    pass
