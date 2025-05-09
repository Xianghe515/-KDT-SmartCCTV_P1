"""empty message

Revision ID: 9dd9c8f9f281
Revises: 
Create Date: 2025-04-15 15:54:48.528902

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9dd9c8f9f281'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.Column('user_name', sa.String(length=100), nullable=False),
    sa.Column('birth_date', sa.Date(), nullable=True),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('phone_number', sa.String(length=15), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('nickname', sa.String(length=100), nullable=True),
    sa.Column('social_platform', sa.String(length=20), nullable=True),
    sa.Column('kakao_access_token', sa.String(length=255), nullable=True),
    sa.Column('kakao_user_id', sa.BigInteger(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('Users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_Users_email'), ['email'], unique=False)
        batch_op.create_index(batch_op.f('ix_Users_kakao_user_id'), ['kakao_user_id'], unique=True)
        batch_op.create_index(batch_op.f('ix_Users_user_name'), ['user_name'], unique=False)

    op.create_table('Cameras',
    sa.Column('camera_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('device_id', sa.String(length=255), nullable=False),
    sa.Column('device_name', sa.String(length=255), nullable=True),
    sa.Column('ip_address', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('camera_id')
    )
    op.create_table('Videos',
    sa.Column('video_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('camera_id', sa.Integer(), nullable=True),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('duration', sa.String(length=50), nullable=True),
    sa.Column('detected_objects', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['camera_id'], ['Cameras.camera_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('video_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Videos')
    op.drop_table('Cameras')
    with op.batch_alter_table('Users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_Users_user_name'))
        batch_op.drop_index(batch_op.f('ix_Users_kakao_user_id'))
        batch_op.drop_index(batch_op.f('ix_Users_email'))

    op.drop_table('Users')
    # ### end Alembic commands ###
