import json
import re


class ResponseParser:
    # Convert the JSON response from Gemini into a python object so that we can use the data
    def convert_to_python_object(self, response):
        match = re.search(r"```json\n(.*?)\n```", response.text, re.DOTALL)

        if match:
            json_content = match.group(1)
            try:
                return json.loads(json_content)
            except json.JSONDecodeError:
                return {"error", "Invalid JSON format"}
        else:
            return response.text
