from app.db.schema import metadata


def test_schema_tracks_playbook_tables() -> None:
    assert set(metadata.tables) == {
        "claim_lines",
        "claim_status_history",
        "claims",
        "declines",
        "enrolment_months",
        "members",
        "plans",
        "premium",
        "providers",
        "reserves",
    }
