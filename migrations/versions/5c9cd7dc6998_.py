"""empty message

Revision ID: 5c9cd7dc6998
Revises: 
Create Date: 2024-10-15 01:06:46.883394

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c9cd7dc6998'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_competition', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_updated_time', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_competition', schema=None) as batch_op:
        batch_op.drop_column('last_updated_time')

    # ### end Alembic commands ###