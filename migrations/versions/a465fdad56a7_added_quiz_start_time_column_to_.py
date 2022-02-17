"""Added quiz_start_time column to quiztemp table

Revision ID: a465fdad56a7
Revises: fbf7caff416e
Create Date: 2022-02-17 15:07:08.650650

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a465fdad56a7'
down_revision = 'fbf7caff416e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('quiztemp',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('qn_id_str', sa.String(length=200), nullable=True),
    sa.Column('answer_str', sa.String(length=500), nullable=True),
    sa.Column('response_str', sa.String(length=500), nullable=True),
    sa.Column('qn_type_str', sa.String(length=500), nullable=True),
    sa.Column('next_qn_id', sa.Integer(), nullable=True),
    sa.Column('quiz_taker_id', sa.Integer(), nullable=True),
    sa.Column('date_added', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('quiztemp')
    # ### end Alembic commands ###
