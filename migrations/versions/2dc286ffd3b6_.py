"""empty message

Revision ID: 2dc286ffd3b6
Revises: cde2cccef39a
Create Date: 2025-04-03 10:40:32.609273

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '2dc286ffd3b6'
down_revision = 'cde2cccef39a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Videos', schema=None) as batch_op:
        batch_op.alter_column('detected_objects',
               existing_type=mysql.VARCHAR(length=50),
               type_=sa.String(length=255),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Videos', schema=None) as batch_op:
        batch_op.alter_column('detected_objects',
               existing_type=sa.String(length=255),
               type_=mysql.VARCHAR(length=50),
               existing_nullable=True)

    # ### end Alembic commands ###
