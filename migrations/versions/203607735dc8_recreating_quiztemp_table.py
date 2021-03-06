"""Recreating quiztemp table

Revision ID: 203607735dc8
Revises: 37c3caaa58d3
Create Date: 2022-02-08 19:34:44.325051

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '203607735dc8'
down_revision = '37c3caaa58d3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('quiztemp',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('qn_id_str', sa.String(length=200), nullable=True),
    sa.Column('answer_str', sa.String(length=500), nullable=True),
    sa.Column('response_str', sa.String(length=500), nullable=True),
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
