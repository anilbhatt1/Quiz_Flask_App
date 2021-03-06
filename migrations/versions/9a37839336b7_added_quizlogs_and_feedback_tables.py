"""Added quizlogs and feedback tables

Revision ID: 9a37839336b7
Revises: 
Create Date: 2022-02-06 18:52:07.452119

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a37839336b7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('feedbacks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('feedback_giver_name', sa.String(length=20), nullable=False),
    sa.Column('feedback_details', sa.String(length=900), nullable=False),
    sa.Column('date_of_feedback', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('quizlogs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('quiz_details', sa.String(length=900), nullable=False),
    sa.Column('date_taken', sa.DateTime(), nullable=True),
    sa.Column('quiz_taker_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['quiz_taker_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('quizlogs')
    op.drop_table('feedbacks')
    # ### end Alembic commands ###
