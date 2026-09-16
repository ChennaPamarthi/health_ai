from health.services.ai_service import AIService


class LLMClient:
    """
    Compatibility wrapper for the old AI entry point.
    All OpenAI calls are delegated to AIService.
    """

    def __init__(self):
        self.ai_service = AIService()

    def generate(self, prompt):
        return self.ai_service.generate_text(prompt)

