"""create universal survey tables

Revision ID: a750e11b4553
Revises: 46bd523c403c
Create Date: 2026-07-22 13:26:53.292780
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# Идентификаторы миграции Alembic.
revision: str = "a750e11b4553"
down_revision: str | Sequence[str] | None = "46bd523c403c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создание универсальной структуры опросов."""

    op.create_table(
        "compass_users",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "compass_user_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "display_name",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "last_group_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "last_message_type",
            sa.String(length=20),
            nullable=True,
        ),
        sa.Column(
            "current_location",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_compass_users_compass_user_id"),
        "compass_users",
        ["compass_user_id"],
        unique=True,
    )

    op.create_table(
        "surveys",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "completion_message",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "interval_days",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_surveys_code"),
        "surveys",
        ["code"],
        unique=True,
    )

    op.create_table(
        "survey_questions",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "survey_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "position",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "text",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "answer_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "required",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "show_if_question_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "show_if_value",
            sa.String(length=255),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["show_if_question_id"],
            ["survey_questions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["survey_id"],
            ["surveys.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "survey_id",
            "code",
            name="uq_survey_questions_survey_code",
        ),
        sa.UniqueConstraint(
            "survey_id",
            "position",
            name="uq_survey_questions_survey_position",
        ),
    )

    op.create_index(
        op.f("ix_survey_questions_survey_id"),
        "survey_questions",
        ["survey_id"],
        unique=False,
    )

    op.create_table(
        "survey_schedules",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "survey_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "next_run_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["survey_id"],
            ["surveys.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["compass_users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "survey_id",
            name="uq_survey_schedules_user_survey",
        ),
    )

    op.create_index(
        op.f("ix_survey_schedules_next_run_at"),
        "survey_schedules",
        ["next_run_at"],
        unique=False,
    )

    op.create_index(
        op.f("ix_survey_schedules_survey_id"),
        "survey_schedules",
        ["survey_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_survey_schedules_user_id"),
        "survey_schedules",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "survey_sessions",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "survey_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "current_question_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["current_question_id"],
            ["survey_questions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["survey_id"],
            ["surveys.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["compass_users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_survey_sessions_current_question_id"),
        "survey_sessions",
        ["current_question_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_survey_sessions_status"),
        "survey_sessions",
        ["status"],
        unique=False,
    )

    op.create_index(
        op.f("ix_survey_sessions_survey_id"),
        "survey_sessions",
        ["survey_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_survey_sessions_user_id"),
        "survey_sessions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "survey_responses",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "value",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["survey_questions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["survey_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id",
            "question_id",
            name="uq_survey_responses_session_question",
        ),
    )

    op.create_index(
        op.f("ix_survey_responses_question_id"),
        "survey_responses",
        ["question_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_survey_responses_session_id"),
        "survey_responses",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    """Удаление универсальной структуры опросов."""

    op.drop_index(
        op.f("ix_survey_responses_session_id"),
        table_name="survey_responses",
    )

    op.drop_index(
        op.f("ix_survey_responses_question_id"),
        table_name="survey_responses",
    )

    op.drop_table("survey_responses")

    op.drop_index(
        op.f("ix_survey_sessions_user_id"),
        table_name="survey_sessions",
    )

    op.drop_index(
        op.f("ix_survey_sessions_survey_id"),
        table_name="survey_sessions",
    )

    op.drop_index(
        op.f("ix_survey_sessions_status"),
        table_name="survey_sessions",
    )

    op.drop_index(
        op.f("ix_survey_sessions_current_question_id"),
        table_name="survey_sessions",
    )

    op.drop_table("survey_sessions")

    op.drop_index(
        op.f("ix_survey_schedules_user_id"),
        table_name="survey_schedules",
    )

    op.drop_index(
        op.f("ix_survey_schedules_survey_id"),
        table_name="survey_schedules",
    )

    op.drop_index(
        op.f("ix_survey_schedules_next_run_at"),
        table_name="survey_schedules",
    )

    op.drop_table("survey_schedules")

    op.drop_index(
        op.f("ix_survey_questions_survey_id"),
        table_name="survey_questions",
    )

    op.drop_table("survey_questions")

    op.drop_index(
        op.f("ix_surveys_code"),
        table_name="surveys",
    )

    op.drop_table("surveys")

    op.drop_index(
        op.f("ix_compass_users_compass_user_id"),
        table_name="compass_users",
    )

    op.drop_table("compass_users")
