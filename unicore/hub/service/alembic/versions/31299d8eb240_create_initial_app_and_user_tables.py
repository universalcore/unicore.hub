"""create initial app and user tables

Revision ID: 31299d8eb240
Revises: 
Create Date: 2015-03-02 12:39:18.787953

"""

# revision identifiers, used by Alembic.
revision = '31299d8eb240'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.Unicode(length=255), nullable=True),
    sa.Column('password', sqlalchemy_utils.types.password.PasswordType(max_length=1094), nullable=True),
    sa.Column('app_data', sqlalchemy_utils.types.json.JSONType(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('apps',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('password', sqlalchemy_utils.types.password.PasswordType(max_length=1094), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('apps')
    op.drop_table('users')
    ### end Alembic commands ###
