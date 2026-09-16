import tempfile
from pathlib import Path

import fitz
from PIL import Image

from .base_agent import BaseAgent
from health.ai.prompt_builder import PromptBuilder
from health.services.ai_service import AIService


class DocumentClassifierAgent(BaseAgent):
    """
    Detects whether the uploaded document is:

    - Printed
    - Handwritten

    Printed
        -> Gemini vision

    Handwritten
        -> OpenAI Vision
    """

    name = "Document Classifier Agent"

    def __init__(self):
        self.ai_service = AIService()

    def can_handle(self, data):
        """
        This agent can classify every uploaded document.
        """
        return True

    def process(self, data):
        """
        Required by BaseAgent.

        Every service should call process() instead of classify().
        """
        return self.classify(data)

    def _prepare_image(self, file_path):
        """
        Converts PDFs into a temporary PNG image.

        Image files are returned unchanged.
        """

        path = Path(file_path)

        if path.suffix.lower() != ".pdf":
            return str(path), None

        with fitz.open(str(path)) as pdf:

            page = pdf.load_page(0)

            pix = page.get_pixmap(dpi=200)

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples,
            )

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".png",
        )

        image.save(temp_file.name)

        temp_file.close()

        return temp_file.name, temp_file.name

    def classify(self, file_path):
        """
        Uses OpenAI Vision to classify the uploaded document.

        Returns

        {
            "classification": "printed",
            "confidence": 0.98,
            "reason": "..."
        }
        """

        image_path, temp_image = self._prepare_image(file_path)

        try:

            result = self.ai_service.analyze_image(
                prompt=PromptBuilder.classification_prompt(),
                file_path=image_path,
                system_prompt=(
                    "You are a document classification assistant.\n"
                    "Determine whether the uploaded medical document is "
                    "PRINTED or HANDWRITTEN.\n\n"
                    "Return JSON ONLY.\n\n"
                    "Example:\n"
                    "{\n"
                    '    "classification":"printed",\n'
                    '    "confidence":0.98,\n'
                    '    "reason":"Document contains computer printed text."\n'
                    "}"
                ),
            )

        finally:

            if temp_image:

                Path(temp_image).unlink(missing_ok=True)

        if not isinstance(result, dict):
            result = {}

        classification = (
            str(result.get("classification", "printed"))
            .strip()
            .lower()
        )

        if classification not in ["printed", "handwritten"]:

            classification = "printed"

        try:

            confidence = float(result.get("confidence", 0))

        except Exception:

            confidence = 0.0

        return {
            "classification": classification,
            "confidence": confidence,
            "reason": result.get("reason", ""),
        }
