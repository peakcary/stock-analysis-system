"""
initial core tables

Revision ID: 20251009_000001
Revises: 
Create Date: 2025-10-09 00:00:01
"""

from alembic import op
import sqlalchemy as sa


revision = '20251009_000001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('membership_type', sa.String(length=20), nullable=False, server_default='free'),
        sa.Column('queries_remaining', sa.Integer, nullable=False, server_default='10'),
        sa.Column('membership_expires_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_membership_type', 'users', ['membership_type'])

    # admin_users
    op.create_table(
        'admin_users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100)),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('1')),
        sa.Column('is_superuser', sa.Boolean, server_default=sa.text('0')),
        sa.Column('last_login', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_admin_users_username', 'admin_users', ['username'])
    op.create_index('ix_admin_users_email', 'admin_users', ['email'])

    # user_queries
    op.create_table(
        'user_queries',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('query_type', sa.String(length=50), nullable=False),
        sa.Column('query_params', sa.JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_user_queries_user_id', 'user_queries', ['user_id'])
    op.create_index('ix_user_queries_query_type', 'user_queries', ['query_type'])

    # payments (simple history table used by user CRUD)
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('payment_type', sa.String(length=50), nullable=False),
        sa.Column('payment_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('payment_method', sa.String(length=50)),
        sa.Column('transaction_id', sa.String(length=100)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime),
    )
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_payment_status', 'payments', ['payment_status'])
    op.create_index('ix_payments_transaction_id', 'payments', ['transaction_id'])

    # payment_packages
    op.create_table(
        'payment_packages',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('package_type', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('price', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('queries_count', sa.Integer, server_default='0'),
        sa.Column('validity_days', sa.Integer, server_default='0'),
        sa.Column('membership_type', sa.String(length=20), server_default='free'),
        sa.Column('description', sa.Text),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('1')),
        sa.Column('sort_order', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('package_type')
    )
    op.create_index('ix_payment_packages_active', 'payment_packages', ['is_active'])
    op.create_index('ix_payment_packages_sort', 'payment_packages', ['sort_order'])

    # payment_orders
    op.create_table(
        'payment_orders',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('package_id', sa.Integer, sa.ForeignKey('payment_packages.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('out_trade_no', sa.String(length=64), nullable=False),
        sa.Column('transaction_id', sa.String(length=64)),
        sa.Column('package_type', sa.String(length=20), nullable=False),
        sa.Column('package_name', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending'),
        sa.Column('payment_method', sa.String(length=30), server_default='wechat_native'),
        sa.Column('prepay_id', sa.String(length=64)),
        sa.Column('code_url', sa.Text),
        sa.Column('h5_url', sa.Text),
        sa.Column('expire_time', sa.DateTime, nullable=False),
        sa.Column('paid_at', sa.DateTime),
        sa.Column('cancelled_at', sa.DateTime),
        sa.Column('refunded_at', sa.DateTime),
        sa.Column('refund_amount', sa.DECIMAL(10, 2), server_default='0'),
        sa.Column('client_ip', sa.String(length=45)),
        sa.Column('user_agent', sa.Text),
        sa.Column('notify_data', sa.JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('out_trade_no')
    )
    op.create_index('ix_payment_orders_user', 'payment_orders', ['user_id'])
    op.create_index('ix_payment_orders_status', 'payment_orders', ['status'])
    op.create_index('ix_payment_orders_created_at', 'payment_orders', ['created_at'])

    # payment_notifications
    op.create_table(
        'payment_notifications',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('out_trade_no', sa.String(length=64), nullable=False),
        sa.Column('transaction_id', sa.String(length=64)),
        sa.Column('notification_type', sa.String(length=20), server_default='payment'),
        sa.Column('return_code', sa.String(length=16)),
        sa.Column('result_code', sa.String(length=16)),
        sa.Column('raw_data', sa.Text, nullable=False),
        sa.Column('is_valid', sa.Boolean, server_default=sa.text('0')),
        sa.Column('processed', sa.Boolean, server_default=sa.text('0')),
        sa.Column('process_result', sa.Text),
        sa.Column('client_ip', sa.String(length=45)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('processed_at', sa.DateTime),
    )
    op.create_index('ix_payment_notifications_out_trade_no', 'payment_notifications', ['out_trade_no'])
    op.create_index('ix_payment_notifications_processed', 'payment_notifications', ['processed'])

    # membership_logs
    op.create_table(
        'membership_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('payment_order_id', sa.Integer, sa.ForeignKey('payment_orders.id', ondelete='SET NULL')),
        sa.Column('action_type', sa.String(length=20), nullable=False),
        sa.Column('old_membership_type', sa.String(length=20)),
        sa.Column('new_membership_type', sa.String(length=20)),
        sa.Column('old_queries_remaining', sa.Integer, server_default='0'),
        sa.Column('new_queries_remaining', sa.Integer, server_default='0'),
        sa.Column('queries_added', sa.Integer, server_default='0'),
        sa.Column('old_expires_at', sa.DateTime),
        sa.Column('new_expires_at', sa.DateTime),
        sa.Column('days_added', sa.Integer, server_default='0'),
        sa.Column('operator_id', sa.Integer),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_membership_logs_user', 'membership_logs', ['user_id'])
    op.create_index('ix_membership_logs_action_type', 'membership_logs', ['action_type'])

    # refund_records
    op.create_table(
        'refund_records',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('payment_order_id', sa.Integer, sa.ForeignKey('payment_orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('out_refund_no', sa.String(length=64), nullable=False),
        sa.Column('refund_id', sa.String(length=64)),
        sa.Column('refund_amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('refund_reason', sa.String(length=255)),
        sa.Column('refund_status', sa.String(length=20), server_default='processing'),
        sa.Column('refund_channel', sa.String(length=32)),
        sa.Column('operator_id', sa.Integer),
        sa.Column('notify_data', sa.JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime),
        sa.UniqueConstraint('out_refund_no')
    )
    op.create_index('ix_refund_records_order', 'refund_records', ['payment_order_id'])
    op.create_index('ix_refund_records_status', 'refund_records', ['refund_status'])

    # daily_trading
    op.create_table(
        'daily_trading',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('original_stock_code', sa.String(length=20), nullable=False),
        sa.Column('normalized_stock_code', sa.String(length=10), nullable=False),
        sa.Column('stock_code', sa.String(length=20), nullable=False),
        sa.Column('trading_date', sa.Date, nullable=False),
        sa.Column('trading_volume', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_stock_date', 'daily_trading', ['stock_code', 'trading_date'])
    op.create_index('idx_date_volume', 'daily_trading', ['trading_date', 'trading_volume'])

    # concept_daily_summary
    op.create_table(
        'concept_daily_summary',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('concept_name', sa.String(length=100), nullable=False),
        sa.Column('trading_date', sa.Date, nullable=False),
        sa.Column('total_volume', sa.Integer, nullable=False),
        sa.Column('stock_count', sa.Integer, nullable=False),
        sa.Column('average_volume', sa.Float, nullable=False),
        sa.Column('max_volume', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_concept_date', 'concept_daily_summary', ['concept_name', 'trading_date'])
    op.create_index('idx_date_total', 'concept_daily_summary', ['trading_date', 'total_volume'])

    # stock_concept_ranking
    op.create_table(
        'stock_concept_ranking',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('stock_code', sa.String(length=20), nullable=False),
        sa.Column('concept_name', sa.String(length=100), nullable=False),
        sa.Column('trading_date', sa.Date, nullable=False),
        sa.Column('trading_volume', sa.Integer, nullable=False),
        sa.Column('concept_rank', sa.Integer, nullable=False),
        sa.Column('concept_total_volume', sa.Integer, nullable=False),
        sa.Column('volume_percentage', sa.Float, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_stock_concept_date', 'stock_concept_ranking', ['stock_code', 'concept_name', 'trading_date'])
    op.create_index('idx_concept_date_rank', 'stock_concept_ranking', ['concept_name', 'trading_date', 'concept_rank'])

    # concept_high_record
    op.create_table(
        'concept_high_record',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('concept_name', sa.String(length=100), nullable=False),
        sa.Column('trading_date', sa.Date, nullable=False),
        sa.Column('total_volume', sa.Integer, nullable=False),
        sa.Column('days_period', sa.Integer, nullable=False),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_concept_date_period', 'concept_high_record', ['concept_name', 'trading_date', 'days_period'])
    op.create_index('idx_date_volume_active', 'concept_high_record', ['trading_date', 'total_volume', 'is_active'])

    # txt_import_record
    op.create_table(
        'txt_import_record',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('trading_date', sa.Date, nullable=False),
        sa.Column('file_size', sa.Integer, nullable=False),
        sa.Column('import_status', sa.String(length=20), nullable=False, server_default='success'),
        sa.Column('imported_by', sa.String(length=50), nullable=False),
        sa.Column('total_records', sa.Integer, server_default='0'),
        sa.Column('success_records', sa.Integer, server_default='0'),
        sa.Column('error_records', sa.Integer, server_default='0'),
        sa.Column('concept_count', sa.Integer, server_default='0'),
        sa.Column('ranking_count', sa.Integer, server_default='0'),
        sa.Column('new_high_count', sa.Integer, server_default='0'),
        sa.Column('import_started_at', sa.DateTime, nullable=False),
        sa.Column('import_completed_at', sa.DateTime),
        sa.Column('calculation_time', sa.Float),
        sa.Column('error_message', sa.Text),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_trading_date_status', 'txt_import_record', ['trading_date', 'import_status'])
    op.create_index('idx_imported_by_date', 'txt_import_record', ['imported_by', 'trading_date'])
    op.create_index('idx_filename', 'txt_import_record', ['filename'])


def downgrade() -> None:
    # Drop in reverse order of creation
    op.drop_table('txt_import_record')
    op.drop_table('concept_high_record')
    op.drop_table('stock_concept_ranking')
    op.drop_table('concept_daily_summary')
    op.drop_table('daily_trading')
    op.drop_table('refund_records')
    op.drop_table('membership_logs')
    op.drop_table('payment_notifications')
    op.drop_table('payment_orders')
    op.drop_table('payment_packages')
    op.drop_table('payments')
    op.drop_table('user_queries')
    op.drop_table('admin_users')
    op.drop_table('users')

