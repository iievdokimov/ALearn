"""wordgroup result match-definitions

Revision ID: 2cd39476f268
Revises: e99437ead80c
Create Date: 2024-07-17 17:30:41.860022

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2cd39476f268'
down_revision = 'e99437ead80c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('word_group', schema=None) as batch_op:
        batch_op.add_column(sa.Column('points_ratio_math_definitions', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('word_group', schema=None) as batch_op:
        batch_op.drop_column('points_ratio_math_definitions')

    # ### end Alembic commands ###