from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),

    path('exercises/', views.exercise_list_view, name='exercise_list'),
    path('exercises/new/', views.exercise_create_view, name='exercise_create'),
    path('exercises/<int:pk>/edit/', views.exercise_update_view, name='exercise_update'),
    path('exercises/<int:pk>/delete/', views.exercise_delete_view, name='exercise_delete'),

    path('workouts/', views.workout_list_view, name='workout_list'),
    path('workouts/new/', views.workout_create_view, name='workout_create'),
    path('workouts/<int:pk>/', views.workout_detail_view, name='workout_detail'),
    path('workouts/<int:pk>/edit/', views.workout_update_view, name='workout_update'),
    path('workouts/<int:pk>/delete/', views.workout_delete_view, name='workout_delete'),

    path('workout-sets/', views.workout_set_list_view, name='workout_set_list'),
    path('workout-sets/new/', views.workout_set_create_view, name='workout_set_create'),
    path('workout-sets/<int:pk>/edit/', views.workout_set_update_view, name='workout_set_update'),
    path('workout-sets/<int:pk>/delete/', views.workout_set_delete_view, name='workout_set_delete'),
]
