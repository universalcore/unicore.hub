"""initial App and User tables

Revision ID: 37312eddf0a9
Revises: 
Create Date: 2015-03-04 12:17:25.599166

"""

# revision identifiers, used by Alembic.
revision = '37312eddf0a9'
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
    sa.Column('title', sa.Unicode(length=255), nullable=False),
    sa.Column('slug', sa.Unicode(length=255), nullable=False),
    sa.Column('password', sqlalchemy_utils.types.password.PasswordType(max_length=1094), nullable=False),
    sa.Column('groups', sqlalchemy_utils.types.scalar_list.ScalarListType(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('apps')
    op.drop_table('users')
    ### end Alembic commands ###