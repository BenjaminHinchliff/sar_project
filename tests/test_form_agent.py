from pathlib import Path
from autogen.code_utils import sys
from pypdf import PdfReader, PdfWriter
import pytest
from sar_project.agents.form_agent import FormManager

TEST_FOLDER = Path("tests")

class TestWeatherAgent:
    @pytest.fixture
    def agent(self):
        return FormManager()

    def test_initialization(self, agent):
        assert agent.name == "form_manager"
        assert agent.role == "Form Manager"
        assert agent.mission_status == "standby"

    def test_process_request(self, agent):
        test_form = TEST_FOLDER / "fall-protection-rescue-plan-form.pdf"
        form = PdfReader(test_form)
        message = {
            "form": form,
            "content": 'fill out this form with basic fall protection plans, hard hats, etc, for a department called "Five Johns Labor Board" as signed by five Johns',
        }
        filled_form: PdfWriter = agent.process_request(message)
        # as a litmus test, just get angry if more than a few text forms go unfilled
        assert (
            len(
                [
                    contents
                    for contents in filled_form.get_form_text_fields().values()
                    if contents == ""
                ]
            )
            < 50
        )
        filled_form_path = TEST_FOLDER / f"{test_form.name}-filled.pdf"
        # write out form for manual inspection
        with open(filled_form_path, "wb") as f:
            filled_form.write(f)
