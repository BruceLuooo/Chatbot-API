from django.urls import path
from .views import ChatAPI

urlpatterns = [
    path('chat/', ChatAPI.as_view(), name='chat'),
]
