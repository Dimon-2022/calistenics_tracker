from django.contrib import admin
from .models import Exercise, Muscle, Workout, WorkoutSet

@admin.register(Muscle)
class MuscleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'get_muscles')
    list_filter = ('category', 'target_muscles')
    search_fields = ('name', 'description')
    filter_horizontal = ('target_muscles',)

    @admin.display(description="Target Muscles")
    def get_muscles(self, obj):
        return ", ".join([m.name for m in obj.target_muscles.all()])

class WorkoutSetInline(admin.TabularInline):
    model = WorkoutSet
    extra = 1

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'started_at', 'finished_at', 'total_duration', 'total_volume')
    list_filter = ('type', 'started_at', 'user')
    search_fields = ('user__username', 'notes')
    inlines = [WorkoutSetInline]


@admin.register(WorkoutSet)
class WorkoutSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'workout', 'exercise', 'reps', 'weight', 'duration', 'rest_time')
    list_filter = ('exercise', 'workout__type')
    search_fields = ('exercise__name', 'workout__user__username')