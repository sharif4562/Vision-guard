"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="student"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("google_sub", sa.String(255), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("grade_level", sa.String(64), nullable=False),
        sa.Column("subjects_json", sa.JSON(), nullable=False),
        sa.Column("learning_goal", sa.String(255), nullable=False),
        sa.Column("preferred_language", sa.String(8), nullable=False),
        sa.Column("theme", sa.String(12), nullable=False),
        sa.Column("leaderboard_opt_in", sa.Boolean(), nullable=False),
        sa.Column("xp", sa.Integer(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("streak_days", sa.Integer(), nullable=False),
        sa.Column("last_active_date", sa.Date(), nullable=False),
        sa.Column("weekly_goal_target", sa.Integer(), nullable=False),
        sa.Column("weekly_progress", sa.Integer(), nullable=False),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("family_id", sa.String(36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "diagram_uploads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("normalized_key", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("width_px", sa.Integer(), nullable=False),
        sa.Column("height_px", sa.Integer(), nullable=False),
        sa.Column("blur_score", sa.Float(), nullable=False),
        sa.Column("contrast_score", sa.Float(), nullable=False),
        sa.Column("quality_status", sa.String(24), nullable=False),
        sa.Column("quality_notes_json", sa.JSON(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("demo_slug", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_diagram_uploads_user_id", "diagram_uploads", ["user_id"])

    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("upload_id", sa.String(36), sa.ForeignKey("diagram_uploads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("demo_slug", sa.String(64), nullable=True),
        sa.Column("subject", sa.String(64), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("reference_answer", sa.Text(), nullable=True),
        sa.Column("language", sa.String(8), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("progress_pct", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        sa.Column("used_fallback", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_analysis_jobs_user_created", "analysis_jobs", ["user_id", "created_at"])
    op.create_index("ix_analysis_jobs_user_subject", "analysis_jobs", ["user_id", "subject"])

    op.create_table(
        "analysis_results",
        sa.Column("job_id", sa.String(36), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("agent1_json", sa.JSON(), nullable=False),
        sa.Column("verified_box_ids_json", sa.JSON(), nullable=False),
        sa.Column("unverified_box_ids_json", sa.JSON(), nullable=False),
        sa.Column("agent2_json", sa.JSON(), nullable=False),
        sa.Column("blank_image_key", sa.String(255), nullable=True),
        sa.Column("schema_version", sa.String(16), nullable=False),
    )

    op.create_table(
        "practice_cards",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("box_id", sa.String(32), nullable=False),
        sa.Column("expected_label", sa.String(160), nullable=False),
        sa.Column("hint_definition", sa.Text(), nullable=False),
        sa.Column("distractors_json", sa.JSON(), nullable=False),
        sa.Column("easiness_factor", sa.Float(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_quality", sa.Integer(), nullable=False),
        sa.UniqueConstraint("user_id", "job_id", "box_id", name="uq_practice_card_user_job_box"),
    )

    op.create_table(
        "practice_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_id", sa.String(36), sa.ForeignKey("practice_cards.id", ondelete="SET NULL"), nullable=True),
        sa.Column("mode", sa.String(24), nullable=False),
        sa.Column("score_pct", sa.Float(), nullable=False),
        sa.Column("xp_awarded", sa.Integer(), nullable=False),
        sa.Column("duration_sec", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "user_badges",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("badge_code", sa.String(64), nullable=False),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "badge_code", name="uq_user_badge"),
    )

    op.create_table(
        "teacher_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("teacher_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("share_token", sa.String(64), nullable=False, unique=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "teacher_links",
        "user_badges",
        "practice_attempts",
        "practice_cards",
        "analysis_results",
        "analysis_jobs",
        "diagram_uploads",
        "password_reset_tokens",
        "refresh_tokens",
        "user_profiles",
        "users",
    ]:
        op.drop_table(table)
