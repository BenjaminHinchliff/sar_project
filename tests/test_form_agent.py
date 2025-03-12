from pathlib import Path
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

    def test_larger_form(self, agent: FormManager) -> None:
        test_form = TEST_FOLDER / "SAR-104-Team Assignment.pdf"
        form = PdfReader(test_form)
        message = {
            "form": form,
            "content": r'''Fill out this team assignment form for the incident called "the great johning of '87" with the following information:
an operational period of 42, assignment number 3. Using resources called the john containment device, the personel should be
John Bellardo, John Clements, John Seng, Johnathan Ventura, John Oliver, and John Planck. They are assigned to use the John containment device
to find the lost johns and ensure they are able to reintegrate into society. This is following previous efforts to dejohnify the area that failed.
Time alloted: 6 hours. Use resonable defaults for remaining fields. This has been John johnerson. Feel free to get creative with the rest of the form.
'''
        }
        filled_form = agent.process_request(message)
        # Best we can easily do here is just check the summary exists
        assert filled_form["summary"].strip() != ""
        filled_form_path = TEST_FOLDER / f"{test_form.name}-filled.pdf"
        # write out form for manual inspection
        with open(filled_form_path, "wb") as f:
            filled_form["form"].write(f)


    def test_process_request(self, agent):
        test_form = TEST_FOLDER / "fall-protection-rescue-plan-form.pdf"
        form = PdfReader(test_form)
        message = {
            "form": form,
            "content": 'fill out this form with basic fall protection plans, hard hats, etc, for a department called "Five Johns Labor Board" as signed by five Johns',
        }
        filled_form = agent.process_request(message)
        # Best we can easily do here is just check the summary exists
        assert filled_form["summary"].strip() != ""
        # as a litmus test, just get angry if more than a few text forms go unfilled
        assert (
            len(
                [
                    contents
                    for contents in filled_form["form"].get_form_text_fields().values()
                    if contents == ""
                ]
            )
            < 50
        )
        filled_form_path = TEST_FOLDER / f"{test_form.name}-filled.pdf"
        # write out form for manual inspection
        with open(filled_form_path, "wb") as f:
            filled_form["form"].write(f)
