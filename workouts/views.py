from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum, F, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Exercise, Workout, WorkoutSet
from .forms import ExerciseSearchForm, ExerciseForm, WorkoutForm, WorkoutSearchForm


@login_required
def dashboard_view(request):
    """Main dashboard showing weekly progress, stats, and top exercises."""
    user = request.user
    now = timezone.now()

    # Time boundaries
    this_week_start = now - timedelta(days=7)
    last_week_start = now - timedelta(days=14)

    this_month_start = now - timedelta(days=30)
    last_month_start = now - timedelta(days=60)

    # 1. Weekly Workouts Comparison
    current_week_workouts = Workout.objects.filter(user=user, started_at__gte=this_week_start).count()
    previous_week_workouts = Workout.objects.filter(
        user=user, started_at__gte=last_week_start, started_at__lt=this_week_start
    ).count()

    if previous_week_workouts > 0:
        weekly_change_pct = round(((current_week_workouts - previous_week_workouts) / previous_week_workouts) * 100, 1)
    else:
        weekly_change_pct = 100.0 if current_week_workouts > 0 else 0.0

    # 2. Monthly Volume Comparison
    current_month_sets = WorkoutSet.objects.filter(workout__user=user, workout__started_at__gte=this_month_start)
    previous_month_sets = WorkoutSet.objects.filter(
        workout__user=user, workout__started_at__gte=last_month_start, workout__started_at__lt=this_month_start
    )

    current_month_volume = current_month_sets.aggregate(total=Sum(F('reps') * F('weight')))['total'] or 0
    previous_month_volume = previous_month_sets.aggregate(total=Sum(F('reps') * F('weight')))['total'] or 0

    if previous_month_volume > 0:
        monthly_volume_pct = round(((current_month_volume - previous_month_volume) / previous_month_volume) * 100, 1)
    else:
        monthly_volume_pct = 100.0 if current_month_volume > 0 else 0.0

    # 3. Top Most Frequent Exercises
    top_frequent_exercises = Exercise.objects.filter(workout_sets__workout__user=user) \
        .annotate(total_sets=Count('workout_sets')) \
        .order_by('-total_sets')[:5]

    # 4. Recent Workouts Summary
    recent_workouts = Workout.objects.filter(user=user).order_by('-started_at')[:5]

    context = {
        'current_week_workouts': current_week_workouts,
        'weekly_change_pct': weekly_change_pct,
        'current_month_volume': current_month_volume,
        'monthly_volume_pct': monthly_volume_pct,
        'top_frequent_exercises': top_frequent_exercises,
        'recent_workouts': recent_workouts,
    }
    return render(request, 'workouts/dashboard.html', context)


@login_required
def exercise_list_view(request):
    """Catalog of global exercises PLUS user's private custom exercises."""
    form = ExerciseSearchForm(request.GET or None)

    exercises = Exercise.objects.filter(
        Q(user__isnull=True) | Q(user=request.user)
    ).prefetch_related('target_muscles')

    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        target_muscles = form.cleaned_data.get('target_muscles')

        if query:
            exercises = exercises.filter(
                Q(name__icontains=query) | Q(description__icontains=query) | Q(target_muscles__name__icontains=query)
            )
        if category:
            exercises = exercises.filter(category=category)
        if target_muscles:
            exercises = exercises.filter(target_muscles__in=target_muscles)

    exercises = exercises.distinct().order_by('name')

    return render(request, 'workouts/exercise_list.html', {
        'form': form,
        'exercises': exercises
    })


@login_required
def exercise_create_view(request):
    """Create a private custom exercise for the logged-in user."""
    if request.method == 'POST':
        form = ExerciseForm(request.POST)
        if form.is_valid():
            exercise = form.save(commit=False)
            exercise.user = request.user
            exercise.save()
            form.save_m2m()
            return redirect('exercise_list')
    else:
        form = ExerciseForm()

    return render(request, 'workouts/exercise_form.html', {'form': form})


@login_required
def workout_list_view(request):
    """List of all user workout sessions with search filters."""
    form = WorkoutSearchForm(request.GET or None)
    workouts = Workout.objects.filter(user=request.user).order_by('-started_at')

    if form.is_valid():
        workout_type = form.cleaned_data.get('type')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')

        if workout_type:
            workouts = workouts.filter(type=workout_type)
        if date_from:
            workouts = workouts.filter(started_at__date__gte=date_from)
        if date_to:
            workouts = workouts.filter(started_at__date__lte=date_to)

    return render(request, 'workouts/workout_list.html', {
        'form': form,
        'workouts': workouts
    })


@login_required
def workout_create_view(request):
    """Create a new workout session."""
    if request.method == 'POST':
        form = WorkoutForm(request.POST)
        if form.is_valid():
            workout = form.save(commit=False)
            workout.user = request.user
            workout.save()
            return redirect('workout_list')
    else:
        form = WorkoutForm()

    return render(request, 'workouts/workout_form.html', {'form': form})


@login_required
def workout_set_list_view(request):
    """Overview list of recorded workout sets."""
    sets = WorkoutSet.objects.filter(workout__user=request.user).select_related('workout', 'exercise').order_by('-id')
    return render(request, 'workouts/workout_set_list.html', {'sets': sets})