from app.demo.runner import SCRIPTED_STEPS, run_demo


def test_scripted_demo_runner_passes(capsys) -> None:
    """Run the guided demo and assert every expected state still passes."""
    result = run_demo(SCRIPTED_STEPS)

    output = capsys.readouterr().out

    assert result == 0
    assert "Vellum-NLQ scripted demo" in output
    assert "Happy path answer" in output
    assert "Clarification before guessing" in output
    assert "Demo finished successfully." in output
