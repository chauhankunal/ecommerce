"""order model addition

Revision ID: 563e2d600018
Revises: d677f2088f54
Create Date: 2024-12-01 03:19:18.976534

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '563e2d600018'
down_revision: Union[str, None] = 'd677f2088f54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('shipping_city', sa.String(), nullable=False))
    op.add_column('orders', sa.Column('shipping_country', sa.String(), nullable=False))
    op.add_column('orders', sa.Column('shipping_postal_code', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('orders', 'shipping_postal_code')
    op.drop_column('orders', 'shipping_country')
    op.drop_column('orders', 'shipping_city')
    # ### end Alembic commands ###
