from chatbot.utils.response_parser import ResponseParser
from chatbot.clients.gemini_client import GeminiClient
from chatbot.services.video_search import VideoSearchService
from chatbot.services.prompts import Prompts

import re

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView


class ChatAPI(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    gemini_client = GeminiClient()
    parse_response = ResponseParser()
    video_search_service = VideoSearchService()

    def post(self, request):
        user_prompt = request.data.get("prompt")
        chat_summary = request.data.get("summary", "")

        if not user_prompt:
            return Response(
                {"error": "No prompt provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        prompt = Prompts.create_initial_prompt(user_prompt, chat_summary)
        gemini_response = self.gemini_client.send_message(prompt)

        if gemini_response:
            formatted_response = self.parse_response.convert_to_python_object(
                gemini_response
            )
            return self.build_response(formatted_response, user_prompt)

        else:
            return Response(
                {"error": "There was an error in generating a response"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def build_response(self, formatted_response, user_prompt):
        intent = formatted_response.get("intent", "")
        summary = formatted_response.get("summary", "")
        text_response = formatted_response.get("response")

        response_data = {
            "summary": summary,
            "text_response": re.sub(
                r"\n.*", "", text_response, flags=re.DOTALL
            ),  # Need to clean the text response because gemini will sometimes provide extra information.
            "video_results": [],
        }
        if intent == "find video":
            query_options = self.get_typesense_query_options(summary, user_prompt)
            video_results = self.video_search_service.find_related_videos(query_options)
            if len(video_results) == 0:
                response_data["text_response"] = (
                    "Sorry, we couldn't find what you were looking for."
                )
            response_data["video_results"] = video_results

        return Response(response_data, status=status.HTTP_200_OK)

    def get_typesense_query_options(self, summary, user_prompt):
        prompt = Prompts.create_video_search_query_prompt(summary, user_prompt)
        generate_query_options = self.gemini_client.send_message(prompt)
        return self.parse_response.convert_to_python_object(generate_query_options)
