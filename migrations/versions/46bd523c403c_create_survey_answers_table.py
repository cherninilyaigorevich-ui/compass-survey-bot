"""create survey answers table

Revision ID: 46bd523c403c
Revises: 
Create Date: 2026-07-21 08:58:35.747744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46bd523c403c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "survey_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("answer", sa.String(length=10), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_survey_answers_id",
        "survey_answers",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_survey_answers_id",
        table_name="survey_answers",
    )

    op.drop_table("survey_answers")
