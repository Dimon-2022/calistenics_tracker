from django.urls import path
from . import views

urlpatterns = [
    path('', views.exercise_list_view, name='exercise_list'),
]