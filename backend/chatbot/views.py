import json
import re
from datetime import datetime

import vertexai
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from vertexai.preview.generative_models import GenerativeModel
from typesense import Client
from typesense.exceptions import TypesenseClientError, ObjectNotFound


project_id = settings.GCP_PROJECT_ID
location = settings.GCP_VERTEX_AI_REGION
ai_model = settings.GCP_VERTEX_AI_MODEL
vertexai.init(project=project_id, location=location)

model = GenerativeModel(ai_model)
chat_with_gemini = model.start_chat()

client = Client(settings.TYPESENSE_CONFIG)


class ChatAPI(APIView):
    def post(self, request):
        user_prompt = request.data.get("prompt")
        chat_summary = request.data.get("summary", "")

        if not user_prompt:
            return Response(
                {"error": "No prompt provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        prompt = self.create_initial_prompt(user_prompt, chat_summary)
        gemini_response = chat_with_gemini.send_message(prompt)

        if gemini_response:
            formatted_response = self.convert_to_python_object(gemini_response)
            return self.build_response(formatted_response, user_prompt)

        else:
            return Response(
                {"error": "There was an error in generating a response"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def build_response(self, formatted_response, user_prompt):
        intent = formatted_response.get("intent", "")
        summary = formatted_response.get("summary")
        text_response = formatted_response.get("response")
        response_data = {
            "summary": summary,
            "text_response": re.sub(r"\\n.*", "", text_response, flags=re.DOTALL),
            "video_results": [],
        }
        if intent == "find video":
            query_options = self.get_typesense_query_options(summary, user_prompt)
            video_results = self.find_related_video_content(query_options)
            if len(video_results) == 0:
                response_data["text_response"] = (
                    "Sorry, we couldn't find what you were looking for."
                )
            response_data["video_results"] = video_results

        return Response(response_data, status=status.HTTP_200_OK)

    def get_typesense_query_options(self, summary, user_prompt):
        prompt = self.create_video_search_query_prompt(summary, user_prompt)
        generate_query_options = chat_with_gemini.send_message(prompt)
        return self.convert_to_python_object(generate_query_options)

    def find_related_video_content(self, query_options):
        """Utilize Typesense to search for video data based on the entities we retrieved from Gemini"""
        topic = query_options.get("topic")

        # If for some reason topic is false, we return an empty array (no videos found) because we
        # won't be able to query typesense with an empty topic.
        if not topic:
            return []

        filter_parts = []

        if query_options.get("view_count"):
            filter_parts.append(f"view_count:{query_options['view_count']}")

        unix_time = self.convert_to_unix_timestamp(query_options)
        if unix_time:
            filter_parts.append(
                f"released_date:<={unix_time['release_date_before']}",
            )
            filter_parts.append(
                f"released_date:>={unix_time['release_date_after']}",
            )

        formatted_typesense_filter = " && ".join(filter_parts)

        search_parameters = {
            "q": topic,
            "query_by": "titles, tags, description",
            "query_by_weight": "3, 2, 1",
            "split_join_tokens": "true",
            "filter_by": formatted_typesense_filter,
            "sort_by": "view_count:desc",
            "num_typos": 2,
            "per_page": 3,
            "include_fields": "id, titles, thumbnail_height, thumbnail_width, thumbnail_url, view_count, released_date",
        }

        try:
            search_results = client.collections["videolists"].documents.search(
                search_parameters
            )
            return [hit["document"] for hit in search_results["hits"]]
        except TypesenseClientError as e:
            return Response(
                {
                    "error": e,
                    "response": "There was an error with fetching data",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except ObjectNotFound:
            return []
        except Exception as e:
            return Response(
                {
                    "error": e,
                    "response": "There was an error",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def convert_to_python_object(self, response):
        """Convert the JSON response from Gemini into a python object so that we can use the data"""
        match = re.search(r"```json\n(.*?)\n```", response.text, re.DOTALL)

        if match:
            json_content = match.group(1)
            try:
                return json.loads(json_content)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON format"}
        else:
            return response.text

    # Typesense is currently storing release_date value as UNIX so we need to convert the ISO time we're receiving from Gemini into UNIX with this method.
    # I'm not expliciting asking Gemini to return the query dates as UNIX because the prompt is not providing accurate UNIX time.
    def convert_to_unix_timestamp(self, time):
        formatted_time = {}
        if time.get("release_date_before"):
            formatted_time["release_date_before"] = int(
                datetime.strptime(
                    f"{time['release_date_before']} 00:00:00", "%Y-%m-%d %H:%M:%S"
                ).timestamp()
            )
        if time.get("release_date_after"):
            formatted_time["release_date_after"] = int(
                datetime.strptime(
                    f"{time['release_date_after']} 00:00:00", "%Y-%m-%d %H:%M:%S"
                ).timestamp()
            )

        return formatted_time

    # PROMPTS
    def create_initial_prompt(self, user_prompt, chat_summary):
        return f"""
            Here is a user's request: {user_prompt}.
            Here is a summary of the previous messages: {chat_summary}. "
            From what you determined was the intent based on both the user's request and summary, match it to one of these options: 'find video', 'find podcast'. 
            If the intent does not match any of the options provided, set the intent to 'others'. 
            Determine if the user's request is related or unrelated to the summary.
            If the user's request is unrelated, create a new summary focusing solely on the current request. 
            Otherwise, update the summary based on the new request in less than 100 words. 
            For instance, if the previous summary is about TED Talks and the new request is about 'videos with Jenna Ortega,' 
            treat these as unrelated and create a new summary. 
            Return a generic response based on the identified intent in less than 20 words. For example, if the intent is to recommend videos, 
            the response could be 'Here are some videos I found.' If the intent is to recommend podcasts, the response could be 'Here are some podcasts I found.' 
            If the user's request is to find a specific video, for example 'can you find me this video 'La photographie pour déjouer clichés et représentations: Adrien Golinelli at TEDxParis',
            return a generic response 'Here is the video you are looking for.'
            If the intent is 'other', return a 5 sentence response answering the question. 
            Return only the analysis in a well-structured JSON format. The JSON should include the following fields: 
            {{"intent": "string", "summary": "string", "response": "string"}}
            No additional text or explanations should be included, just the JSON.
        """

    def create_video_search_query_prompt(self, chat_summary, user_prompt):
        examples = """
            'can you find me videos that came out two years ago': release_date_before:'2022-12-31', release_date_after:'2022-01-01',
            'can you find me cooking videos that came out last week': release_date_before:'2024-10-29', release_date_after:'2024-10-22',
            'can you find videos released this year': release_date_before:'2024-12-31', release_date_after:'2024-01-01',
            'can you find music videos released in 2022': release_date_before:'2023-12-31', release_date_after:'2023-01-01'
            'can you find me videos from 2023': release_date_before:'2023-12-31', release_date_after:'2023-01-01',
            'can you find me a video that came out on May 12, 2023': release_date_before:'2023-05-12', release_date_after:'2023-05-12'
        """

        return f"""
            summary: {chat_summary}. User Prompt: {user_prompt}. The intent of this is to find videos. Based off the summary and user 
            prompt I would like you to create a JSON Object with these fields and fill any of the values if it's mentioned in the sentence: 
            {{ topic: string, view_count: string, release_date_before: string, release_date_after: string }} 
            If there is a released date mentioned, return it in this format: Year-Month-Day. Here are some phrases that may be found in the user prompt 
            and the results I expect: {examples}.  If a view count is mentioned, format it like 
            these examples:'1000000' -> '1000000''less than 23495' -> '<23495''more than 1240' -> '>1240'
            No additional text or explanations should be included, just the JSON.
        """
