"""NParameters Migration

Revision ID: a86d76e5acd8
Revises: 086afd4fedfa
Create Date: 2022-06-02 17:56:33.488464

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a86d76e5acd8'
down_revision = '086afd4fedfa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('models', sa.Column('parameterorder', sa.String(length=50), nullable=True))
    op.add_column('models', sa.Column('numberofparameters', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('models', 'numberofparameters')
    op.drop_column('models', 'parameterorder')
    # ### end Alembic commands ###
