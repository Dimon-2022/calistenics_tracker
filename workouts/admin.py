from django.contrib import admin
from django.db.models import Count, Sum
from .models import Exercise, Muscle, Workout, WorkoutSet

@admin.register(Muscle)
class MuscleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'metric_type', 'user', 'get_muscles')
    list_filter = ('category', 'metric_type', 'target_muscles')
    search_fields = ('name', 'description')
    filter_horizontal = ('target_muscles',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('target_muscles')

    @admin.display(description="Target Muscles")
    def get_muscles(self, obj):
        return ", ".join([m.name for m in obj.target_muscles.all()])

class WorkoutSetInline(admin.TabularInline):
    model = WorkoutSet
    extra = 1

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'started_at', 'finished_at', 'total_duration', 'sets_count', 'total_reps')
    list_filter = ('type', 'started_at', 'user')
    search_fields = ('user__username', 'notes')
    inlines = [WorkoutSetInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').annotate(
            _sets_count=Count('sets'), _total_reps=Sum('sets__reps')
        )

    @admin.display(description="Sets", ordering='_sets_count')
    def sets_count(self, obj):
        return obj._sets_count

    @admin.display(description="Total reps", ordering='_total_reps')
    def total_reps(self, obj):
        return obj._total_reps or 0


@admin.register(WorkoutSet)
class WorkoutSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'workout', 'exercise', 'set_number', 'reps', 'weight', 'duration', 'rest_time', 'rpe')
    list_filter = ('exercise', 'workout__type')
    search_fields = ('exercise__name', 'workout__user__username')
    list_select_related = ('workout', 'exercise')
