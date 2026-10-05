from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('exercises/', views.exercise_list_view, name='exercise_list'),
    path('exercises/new/', views.exercise_create_view, name='exercise_create'),
    path('workouts/', views.workout_list_view, name='workout_list'),
    path('workouts/new/', views.workout_create_view, name='workout_create'),
    path('workout-sets/', views.workout_set_list_view, name='workout_set_list'),
]