"""Initial schema - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-24 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create candles table
    op.create_table(
        'candles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timeframe', sa.String(length=5), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('open', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('high', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('low', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('close', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('volume', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'timeframe', 'timestamp', name='uix_candle_unique')
    )
    op.create_index('idx_candles_lookup', 'candles', ['symbol', 'timeframe', 'timestamp'], unique=False)
    op.create_index(op.f('ix_candles_id'), 'candles', ['id'], unique=False)
    op.create_index(op.f('ix_candles_symbol'), 'candles', ['symbol'], unique=False)
    op.create_index(op.f('ix_candles_timeframe'), 'candles', ['timeframe'], unique=False)
    op.create_index(op.f('ix_candles_timestamp'), 'candles', ['timestamp'], unique=False)

    # Create trades table
    op.create_table(
        'trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('direction', sa.String(length=4), nullable=False),
        sa.Column('strike', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('option_type', sa.String(length=2), nullable=False),
        sa.Column('entry_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('entry_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('entry_spot_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('exit_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('exit_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('exit_spot_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('exit_reason', sa.String(length=50), nullable=True),
        sa.Column('stop_loss', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('take_profit', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('position_size', sa.Integer(), nullable=False),
        sa.Column('pnl', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('pnl_r', sa.Numeric(precision=5, scale=3), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('entry_filters', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_trades_entry_time', 'trades', ['entry_time'], unique=False)
    op.create_index('idx_trades_status', 'trades', ['status'], unique=False)
    op.create_index(op.f('ix_trades_id'), 'trades', ['id'], unique=False)

    # Create account_state table
    op.create_table(
        'account_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('starting_capital', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('ending_capital', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('daily_pnl', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('daily_pnl_r', sa.Numeric(precision=5, scale=3), nullable=True),
        sa.Column('trades_count', sa.Integer(), nullable=True),
        sa.Column('wins', sa.Integer(), nullable=True),
        sa.Column('losses', sa.Integer(), nullable=True),
        sa.Column('kill_switch_triggered', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', name='uix_account_date')
    )
    op.create_index(op.f('ix_account_state_date'), 'account_state', ['date'], unique=True)
    op.create_index(op.f('ix_account_state_id'), 'account_state', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_account_state_id'), table_name='account_state')
    op.drop_index(op.f('ix_account_state_date'), table_name='account_state')
    op.drop_table('account_state')
    
    op.drop_index(op.f('ix_trades_id'), table_name='trades')
    op.drop_index('idx_trades_status', table_name='trades')
    op.drop_index('idx_trades_entry_time', table_name='trades')
    op.drop_table('trades')
    
    op.drop_index(op.f('ix_candles_timestamp'), table_name='candles')
    op.drop_index(op.f('ix_candles_timeframe'), table_name='candles')
    op.drop_index(op.f('ix_candles_symbol'), table_name='candles')
    op.drop_index(op.f('ix_candles_id'), table_name='candles')
    op.drop_index('idx_candles_lookup', table_name='candles')
    op.drop_table('candles')
