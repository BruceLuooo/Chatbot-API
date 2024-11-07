from django.conf import settings
from vertexai.preview.generative_models import GenerativeModel
import vertexai


class GeminiClient:
    def __init__(self):
        project_id = settings.GCP_PROJECT_ID
        location = settings.GCP_VERTEX_AI_REGION
        ai_model = settings.GCP_VERTEX_AI_MODEL
        vertexai.init(project=project_id, location=location)

        self.model = GenerativeModel(ai_model)
        self.chat = self.model.start_chat()

    def send_message(self, prompt):
        return self.chat.send_message(prompt)
