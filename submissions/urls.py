from django.urls import path
from .views import run_view,submit_view

urlpatterns = [
    path('run',run_view),
    path('submit',submit_view)
]
