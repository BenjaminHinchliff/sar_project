import os
from pypdf import PdfReader, PdfWriter
import google.generativeai as genai
import dotenv
import editdistance

from sar_project.agents.base_agent import SARBaseAgent

dotenv.load_dotenv()
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])


class FormManager(SARBaseAgent):
    def __init__(self, name="form_manager"):
        super().__init__(
            name=name,
            role="Form Manager",
            system_message="""You are a form filing assistant. Your role is to:
            1. Understand a given form
            2. Understand the values to fill, provided by a user
            3. Fill them in appropriately""",
        )
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def process_request(
        self, message: dict[str, PdfReader | str]
    ) -> PdfWriter | dict[str, str]:
        """Process weather-related requests"""
        try:
            if "form" not in message or not isinstance(message["form"], PdfReader):
                raise RuntimeError("message must contain form")
            elif "content" not in message or not isinstance(message["content"], str):
                raise RuntimeError("message must contain content")
            return self.fill_form(message["form"], message["content"])
        except Exception as e:
            return {"error": str(e)}

    def fill_form(self, reader: PdfReader, content_prompt: str) -> dict[str, PdfWriter | str]:
        writer = PdfWriter()
        writer.append(reader)
        text = "\n".join(page.extract_text() for page in reader.pages)
        fields = reader.get_form_text_fields()
        prompt = f"""With this form:
{text}

And this prompt for how the form should be filled:
{content_prompt}

Give form context appropriate content for each of following fields with each field on a separate line separated by a colon. Do not fill in any information that isn't in the content prompt or reasonably inferred from it. After writing the content, write <END> and then summarize what was written.
example field: example content
\"{", ".join(fields)}\":
"""
        text = self.model.generate_content(prompt).text
        # FIXME: could put more validation and retry logic here but that's kind of an infinite time sink
        filled_fields_raw, summary = text.split("<END>", 2)
        filled_fields = {
            e[0]: e[1] if len(e) > 1 else ""
            for e in (line.split(":", 2) for line in filled_fields_raw.splitlines())
        }
        filled_fields = {
            self.autocorrect_field(f, list(fields.keys())): v
            for f, v in filled_fields.items()
        }
        for page in writer.pages:
            writer.update_page_form_field_values(
                page, filled_fields, auto_regenerate=False
            )
        return {
            "form": writer,
            "summary": summary,
        }

    def autocorrect_field(
        self, field: str, candidates: list[str], threshold: int = 10
    ) -> str:
        candidates = sorted(candidates, key=lambda c: editdistance.eval(c, field))
        if editdistance.eval(candidates[0], field) < threshold:
            return candidates[0]
        else:
            return field

    def update_status(self, status):
        """Update the agent's status"""
        self.status = status
        return {"status": "updated", "new_status": status}

    def get_status(self):
        """Get the agent's current status"""
        return getattr(self, "status", "unknown")
