from vosyn_assist.clients.typesense_client import TypesenseClient
from datetime import datetime


class VideoSearchService:
    def __init__(self):
        self.typesense = TypesenseClient()

    # Utilize Typesense to search for video data based on the entities we retrieved from Gemini
    def find_related_videos(self, query_options):
        topic = query_options.get('topic', "")

        if not topic:
            return []
        
        filters = self.build_filter(query_options)

        search_parameters = {
            "q": topic,
            "query_by": "titles, tags, description",
            "query_by_weight": "3, 2, 1",
            "split_join_tokens": "true",
            "filter_by": filters,
            "sort_by": "view_count:desc",
            "num_typos": 2,
            "per_page": 3,
            "include_fields": "id, titles, thumbnail_height, thumbnail_width, thumbnail_url, view_count, released_date",
        }
        search_results = self.typesense.client.collections["videolists"].documents.search(
            search_parameters
        )

        return [hit["document"] for hit in search_results["hits"]]
    
    def build_filter(self, query_options):
        filter_parts = []

        if query_options["view_count"]:
            filter_parts.append(f'view_count:{query_options['view_count']}')
        
        unix_time = self.convert_to_unix_timestamp(query_options)

        if unix_time:
            filter_parts.append(
                f'released_date:<={unix_time['release_date_before']}'
            )
            filter_parts.append(
                f'released_date:>={unix_time['release_date_after']}'
            )

        return " && ".join(filter_parts)

    # Typesense is currently storing release_date value as UNIX so we need to convert the ISO time we're receiving from Gemini into UNIX with this method.
    # I'm not expliciting asking Gemini to return the query dates as UNIX because the prompt is not providing accurate UNIX time.
    def convert_to_unix_timestamp(self, time):
        formatted_time = {}
        if time["release_date_before"]:
            formatted_time["release_date_before"] = int(
                datetime.strptime(
                    f'{time['release_date_before']} 00:00:00', "%Y-%m-%d %H:%M:%S"
                ).timestamp()
            )
        if time["release_date_after"]:
            formatted_time["release_date_after"] = int(
                datetime.strptime(
                    f'{time['release_date_after']} 00:00:00', "%Y-%m-%d %H:%M:%S"
                ).timestamp()
            )

        return formatted_time
