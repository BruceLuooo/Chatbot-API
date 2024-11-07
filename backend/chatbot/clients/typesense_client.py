from typesense import Client
from django.conf import settings


class TypesenseClient:
    def __init__(self):
        self.client = Client(settings.TYPESENSE_CONFIG)