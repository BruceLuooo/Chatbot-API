from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from knox.auth import AuthToken
from rest_framework import status
from unittest.mock import patch
from django.contrib.auth import get_user_model

User = get_user_model()


class VosynAssist(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="a@a.com", password="a@a12345")
        cls.user.first_name, cls.user.last_name = "John", "Doe"
        cls.user.save()
        cls.token = AuthToken.objects.create(cls.user)[1]

        cls.client = APIClient()

        cls.mock_data = [
            {
                "document": {
                    "id": "9d2ecec7-aa6a-4f95-9f5d-9f57fe2a7e3e",
                    "released_date": 1712192027,
                    "thumbnail_height": 360,
                    "thumbnail_url": "https://i.ytimg.com/vi/8S0FDjFBj8o/hqdefault.jpg",
                    "thumbnail_width": 480,
                    "titles": [
                        "How to sound smart in your TEDx Talk | Will Stephen | TEDxNewYork"
                    ],
                    "view_count": 13854313,
                },
                "highlight": {
                    "titles": [
                        {
                            "matched_tokens": ["Talk"],
                            "snippet": "How to sound smart in your TEDx <mark>Talk</mark> | Will Stephen | TEDxNewYork",
                        }
                    ]
                },
                "highlights": [
                    {
                        "field": "titles",
                        "indices": [0],
                        "matched_tokens": [["Talk"]],
                        "snippets": [
                            "How to sound smart in your TEDx <mark>Talk</mark> | Will Stephen | TEDxNewYork"
                        ],
                    }
                ],
                "text_match": 1157451470904229994,
                "text_match_info": {
                    "best_field_score": "2211897606144",
                    "best_field_weight": 13,
                    "fields_matched": 2,
                    "num_tokens_dropped": 0,
                    "score": "1157451470904229994",
                    "tokens_matched": 2,
                    "typo_prefix_score": 0,
                },
            },
            {
                "document": {
                    "id": "649b6211-a71c-4b1a-bd7a-7eac876a7af2",
                    "released_date": 1712196719,
                    "thumbnail_height": 360,
                    "thumbnail_url": "https://i.ytimg.com/vi/qzR62JJCMBQ/hqdefault.jpg",
                    "thumbnail_width": 480,
                    "titles": [
                        "All it takes is 10 mindful minutes | Andy Puddicombe | TED"
                    ],
                    "view_count": 5022422,
                },
                "highlight": {
                    "titles": [
                        {
                            "matched_tokens": ["TED"],
                            "snippet": "All it takes is 10 mindful minutes | Andy Puddicombe | <mark>TED</mark>",
                        }
                    ]
                },
                "highlights": [
                    {
                        "field": "titles",
                        "indices": [0],
                        "matched_tokens": [["TED"]],
                        "snippets": [
                            "All it takes is 10 mindful minutes | Andy Puddicombe | <mark>TED</mark>"
                        ],
                    }
                ],
                "text_match": 1157451436544491626,
                "text_match_info": {
                    "best_field_score": "2211880828928",
                    "best_field_weight": 13,
                    "fields_matched": 2,
                    "num_tokens_dropped": 0,
                    "score": "1157451436544491626",
                    "tokens_matched": 2,
                    "typo_prefix_score": 1,
                },
            },
            {
                "document": {
                    "id": "b98f6344-0466-4958-b328-c20591a24fba",
                    "released_date": 1712192012,
                    "thumbnail_height": 360,
                    "thumbnail_url": "https://i.ytimg.com/vi/80UVjkcxGmA/hqdefault.jpg",
                    "thumbnail_width": 480,
                    "titles": [
                        "How I Overcame My Fear of Public Speaking | Danish Dhamani | TEDxKids@SMU"
                    ],
                    "view_count": 4761397,
                },
                "highlight": {},
                "highlights": [],
                "text_match": 1157451470367359081,
                "text_match_info": {
                    "best_field_score": "2211897344000",
                    "best_field_weight": 13,
                    "fields_matched": 1,
                    "num_tokens_dropped": 0,
                    "score": "1157451470367359081",
                    "tokens_matched": 2,
                    "typo_prefix_score": 0,
                },
            },
        ]

    @patch("vosyn_assist.clients.typesense_client.TypesenseClient")
    def test_retrieve_response_from_vosyn_assist(self, mock_typesense_client):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

        mock_typesense_client.collections[
            "videolists"
        ].documents.search.return_value = {"hits": self.mock_data}

        post_data = {"prompt": "can you find me ted talk videos"}

        response = self.client.post(reverse("chat"), post_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data["text_response"]) > 0)
        self.assertTrue(len(response.data["summary"]) > 0)
        self.assertTrue(response.data["video_results"])

    def test_empty_prompt(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

        post_data = {"prompt": None}
        response = self.client.post(reverse("chat"), post_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_text_only_response(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

        post_data = {"prompt": "who was the president in 2012?"}
        response = self.client.post(reverse("chat"), post_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data["text_response"], str)
        self.assertTrue(len(response.data["text_response"]) > 0)
        self.assertEqual(response.data["video_results"], [])
