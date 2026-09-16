from .llm_service import LLMClient
from .parser import JSONParser
from .prompt_builder import PromptBuilder
from .validator import AIValidator


class PrescriptionExtractor:
    MAX_RETRIES = 2

    def __init__(self):
        self.client = LLMClient()

    def extract(self, text, document_type="Other"):
        prompt = PromptBuilder.document_prompt(text, document_type=document_type)
        last_error = None

        for _ in range(self.MAX_RETRIES):
            try:
                response = self.client.generate(prompt)
                parsed = JSONParser.parse(response)
                validated = AIValidator.validate(parsed)
                return {
                    "success": True,
                    "data": validated,
                }
            except Exception as error:
                last_error = error

        return {
            "success": False,
            "error": str(last_error),
            "data": {
                "document_type": document_type,
                "medicines": [],
            },
        }

    def extract_document(self, document):
        return self.extract(
            document.extracted_text,
            document_type=document.document_type,
        )
