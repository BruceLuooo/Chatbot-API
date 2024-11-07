# PROMPTS
class Prompts:
    @staticmethod
    def create_initial_prompt(user_prompt, chat_summary):
        return (
            f"Here is a user's request: {user_prompt}. "
            f"Here is a summary of the previous messages: {chat_summary}. "
            "From what you determined was the intent based on both the user's request and summary, match it to one of these options: 'find video', 'find podcast'. "
            "If the intent does not match any of the options provided, set the intent to 'others'. "
            "Determine if the user's request is related or unrelated to the summary."
            "If the user's request is unrelated, create a new summary focusing solely on the current request. "
            "Otherwise, update the summary based on the new request in less than 100 words. "
            "For instance, if the previous summary is about TED Talks and the new request is about 'videos with Jenna Ortega,' "
            "treat these as unrelated and create a new summary. "
            "Return a generic response based on the identified intent in less than 100 words. For example, if the intent is to recommend videos, "
            "the response could be 'Here are some videos I found.' If the intent is to recommend podcasts, the response could be 'Here are some podcasts I found.' "
            "If the user's request is to find a specific video, for example 'can you find me this video 'La photographie pour déjouer clichés et représentations: Adrien Golinelli at TEDxParis',"
            "return a generic response 'Here is the video you are looking for.'"
            "If the response you were planning on generating has more than 100 words and the intent you found matched to 'others', "
            "return the response: 'Sorry, I am unable to process queries with outputs over 100 words at this time. Please try another query.'. "
            "Return only the analysis in a well-structured JSON format. The JSON should include the following fields: "
            '{"intent": "string", "summary": "string", "response": "string"} '
            "No additional text or explanations should be included, just the JSON."
        )
    
    @staticmethod
    def create_video_search_query_prompt(chat_summary, user_prompt):
        examples = (
            "'can you find me videos that came out two years ago': release_date_before:'2022-12-31', release_date_after:'2022-01-01',"
            "'can you find me cooking videos that came out last week': release_date_before:'2024-10-29', release_date_after:'2024-10-22',"
            "'can you find videos released this year': release_date_before:'2024-12-31', release_date_after:'2024-01-01',"
            "'can you find music videos released in 2022': release_date_before:'2023-12-31', release_date_after:'2023-01-01'"
            "'can you find me videos from 2023': release_date_before:'2023-12-31', release_date_after:'2023-01-01',"
            "'can you find me a video that came out on May 12, 2023': release_date_before:'2023-05-12', release_date_after:'2023-05-12'"
        )

        return (
            f"summary: {chat_summary}. User Prompt: {user_prompt}. The intent of this is to find videos. Based off the summary and user "
            "prompt I would like you to create a JSON Object with these fields and fill any of the values if it's mentioned in the sentence: "
            "{ topic: string, view_count: string, release_date_before: string, release_date_after: string } "
            "If there is a released date mentioned, return it in this format: Year-Month-Day. Here are some phrases that may be found in the user prompt "
            f"and the results I expect: {examples}.  If a view count is mentioned, format it like "
            "these examples:'1000000' -> '1000000''less than 23495' -> '<23495''more than 1240' -> '>1240'"
            "No additional text or explanations should be included, just the JSON."
        )
