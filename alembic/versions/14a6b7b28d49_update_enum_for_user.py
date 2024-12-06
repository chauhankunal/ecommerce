"""Update enum for user

Revision ID: 14a6b7b28d49
Revises: 0dc31bce188d
Create Date: 2024-11-30 16:56:31.467033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14a6b7b28d49'
down_revision: Union[str, None] = '0dc31bce188d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create a new enum type
    op.execute("CREATE TYPE userrole_new AS ENUM ('CUSTOMER', 'SELLER', 'ADMIN')")
    
    # Add a temporary column with the new enum type
    op.execute("ALTER TABLE users ADD COLUMN role_new userrole_new")
    
    # Update the temporary column with uppercase values
    op.execute("UPDATE users SET role_new = UPPER(role::text)::userrole_new")
    
    # Drop the old column and rename the new one
    op.execute("ALTER TABLE users DROP COLUMN role")
    op.execute("ALTER TABLE users RENAME COLUMN role_new TO role")
    
    # Drop the old enum type
    op.execute("DROP TYPE userrole")
    
    # Rename the new enum type to the original name
    op.execute("ALTER TYPE userrole_new RENAME TO userrole")

def downgrade():
    # Create the old enum type
    op.execute("CREATE TYPE userrole_old AS ENUM ('customer', 'seller', 'admin')")
    
    # Add a temporary column with the old enum type
    op.execute("ALTER TABLE users ADD COLUMN role_old userrole_old")
    
    # Update the temporary column with lowercase values
    op.execute("UPDATE users SET role_old = LOWER(role::text)::userrole_old")
    
    # Drop the new column and rename the old one
    op.execute("ALTER TABLE users DROP COLUMN role")
    op.execute("ALTER TABLE users RENAME COLUMN role_old TO role")
    
    # Drop the new enum type
    op.execute("DROP TYPE userrole")
    
    # Rename the old enum type back to the original name
    op.execute("ALTER TYPE userrole_old RENAME TO userrole")
