"""added post_img to the blogpost model

Revision ID: f3c754905b9e
Revises: f3576ca73f6c
Create Date: 2023-01-09 06:40:43.233515

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3c754905b9e'
down_revision = 'f3576ca73f6c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('blog_post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('post_img', sa.String(), nullable=True))
        batch_op.alter_column('content',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('blog_post', schema=None) as batch_op:
        batch_op.alter_column('content',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.drop_column('post_img')

    # ### end Alembic commands ###