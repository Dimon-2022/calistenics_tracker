from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, ProtectedError, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import (
    ExerciseForm,
    ExerciseSearchForm,
    WorkoutForm,
    WorkoutSearchForm,
    WorkoutSetForm,
    WorkoutSetFormSet,
    WorkoutSetSearchForm,
)
from .models import Exercise, Workout, WorkoutSet
from .stats import dashboard_stats

PAGE_SIZE = 20


def _paginate(request, queryset):
    return Paginator(queryset, PAGE_SIZE).get_page(request.GET.get('page'))


def _filter_date_range(queryset, field, date_from, date_to):
    """Filter by local dates using datetime bounds (`__date` needs MySQL tz tables)."""
    if date_from:
        queryset = queryset.filter(**{f'{field}__gte': timezone.make_aware(datetime.combine(date_from, time.min))})
    if date_to:
        next_day = datetime.combine(date_to + timedelta(days=1), time.min)
        queryset = queryset.filter(**{f'{field}__lt': timezone.make_aware(next_day)})
    return queryset


# ==========================================
# DASHBOARD
# ==========================================

@login_required
def dashboard_view(request):
    """Progress charts and percentages for week / month / year, plus top exercises."""
    stats = dashboard_stats(request.user, request.GET.get('period', 'week'))
    stats['recent_workouts'] = (
        Workout.objects.filter(user=request.user)
        .annotate(sets_count=Count('sets'), total_reps=Sum('sets__reps'))[:5]
    )
    return render(request, 'workouts/dashboard.html', stats)


# ==========================================
# EXERCISES
# ==========================================

@login_required
def exercise_list_view(request):
    """Catalog of global exercises PLUS user's private custom exercises."""
    form = ExerciseSearchForm(request.GET or None)
    exercises = Exercise.objects.available_for(request.user).prefetch_related('target_muscles')

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
        if form.cleaned_data.get('only_custom'):
            exercises = exercises.filter(user=request.user)

    exercises = exercises.distinct().order_by('name')

    return render(request, 'workouts/exercise_list.html', {
        'form': form,
        'exercises': exercises,
    })


@login_required
def exercise_create_view(request):
    """Create a private custom exercise for the logged-in user."""
    form = ExerciseForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        exercise = form.save(commit=False)
        exercise.user = request.user
        exercise.save()
        form.save_m2m()
        messages.success(request, f'Exercise "{exercise.name}" added.')
        return redirect('exercise_list')

    return render(request, 'workouts/exercise_form.html', {'form': form})


@login_required
def exercise_update_view(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk, user=request.user)
    form = ExerciseForm(request.POST or None, instance=exercise, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Exercise "{exercise.name}" updated.')
        return redirect('exercise_list')

    return render(request, 'workouts/exercise_form.html', {'form': form, 'exercise': exercise})


@login_required
@require_POST
def exercise_delete_view(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk, user=request.user)
    try:
        exercise.delete()
        messages.success(request, f'Exercise "{exercise.name}" deleted.')
    except ProtectedError:
        messages.error(request, f'"{exercise.name}" is used in your workout history and cannot be deleted.')
    return redirect('exercise_list')


# ==========================================
# WORKOUTS
# ==========================================

@login_required
def workout_list_view(request):
    """List of all user workout sessions with search filters."""
    form = WorkoutSearchForm(request.GET or None)
    workouts = Workout.objects.filter(user=request.user)

    if form.is_valid():
        workout_type = form.cleaned_data.get('type')
        muscle = form.cleaned_data.get('muscle')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')

        if workout_type:
            workouts = workouts.filter(type=workout_type)
        if muscle:
            workouts = workouts.filter(sets__exercise__target_muscles=muscle).distinct()
        workouts = _filter_date_range(workouts, 'started_at', date_from, date_to)

    workouts = workouts.annotate(
        sets_count=Count('sets', distinct=True),
        exercises_count=Count('sets__exercise', distinct=True),
        total_reps=Sum('sets__reps'),
    ).order_by('-started_at')

    return render(request, 'workouts/workout_list.html', {
        'form': form,
        'page_obj': _paginate(request, workouts),
    })


@login_required
def workout_detail_view(request, pk):
    """Full breakdown of one session: exercises, sets, muscles, rest."""
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    sets = list(workout.sets.select_related('exercise').prefetch_related('exercise__target_muscles').order_by('id'))

    # Group sets by exercise, keeping the order in which exercises were performed.
    groups = {}
    for s in sets:
        group = groups.setdefault(s.exercise_id, {'exercise': s.exercise, 'sets': []})
        group['sets'].append(s)
    for group in groups.values():
        group['total_reps'] = sum(s.reps or 0 for s in group['sets'])

    muscles = sorted({m.name for s in sets for m in s.exercise.target_muscles.all()})
    total_rest = sum((s.rest_time for s in sets if s.rest_time), timedelta())

    return render(request, 'workouts/workout_detail.html', {
        'workout': workout,
        'groups': groups.values(),
        'muscles': muscles,
        'sets_count': len(sets),
        'total_reps': sum(s.reps or 0 for s in sets),
        'total_rest': total_rest,
    })


def _workout_form_view(request, workout=None):
    """Shared create/edit logic for a workout with its sets."""
    form = WorkoutForm(request.POST or None, instance=workout)
    formset = WorkoutSetFormSet(
        request.POST or None,
        instance=workout or Workout(),
        prefix='sets',
        form_kwargs={'user': request.user},
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            workout = form.save(commit=False)
            workout.user = request.user
            workout.save()
            formset.instance = workout
            formset.save()
        messages.success(request, 'Workout saved.')
        return redirect('workout_detail', pk=workout.pk)

    return render(request, 'workouts/workout_form.html', {
        'form': form,
        'formset': formset,
        'workout': workout,
    })


@login_required
def workout_create_view(request):
    return _workout_form_view(request)


@login_required
def workout_update_view(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    return _workout_form_view(request, workout)


@login_required
def workout_delete_view(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    if request.method == 'POST':
        workout.delete()
        messages.success(request, 'Workout deleted.')
        return redirect('workout_list')
    return render(request, 'workouts/workout_confirm_delete.html', {'workout': workout})


# ==========================================
# WORKOUT SETS
# ==========================================

@login_required
def workout_set_list_view(request):
    """Journal of recorded sets with filters."""
    form = WorkoutSetSearchForm(request.GET or None, user=request.user)
    sets = WorkoutSet.objects.filter(workout__user=request.user).select_related('workout', 'exercise')

    if form.is_valid():
        exercise = form.cleaned_data.get('exercise')
        muscle = form.cleaned_data.get('muscle')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')

        if exercise:
            sets = sets.filter(exercise=exercise)
        if muscle:
            sets = sets.filter(exercise__target_muscles=muscle)
        sets = _filter_date_range(sets, 'workout__started_at', date_from, date_to)

    sets = sets.order_by('-workout__started_at', 'id')

    return render(request, 'workouts/workout_set_list.html', {
        'form': form,
        'page_obj': _paginate(request, sets),
    })


def _set_form_view(request, workout_set=None):
    initial = {}
    if workout_set is None and request.GET.get('workout'):
        initial['workout'] = request.GET['workout']
    form = WorkoutSetForm(request.POST or None, instance=workout_set, initial=initial, user=request.user)

    if request.method == 'POST' and form.is_valid():
        workout_set = form.save()
        messages.success(request, f'Set saved: {workout_set.exercise.name} #{workout_set.set_number}.')
        if request.POST.get('add_another'):
            return redirect(f"{request.path}?workout={workout_set.workout_id}")
        return redirect('workout_detail', pk=workout_set.workout_id)

    return render(request, 'workouts/workout_set_form.html', {
        'form': form,
        'workout_set': workout_set,
        'has_workouts': Workout.objects.filter(user=request.user).exists(),
    })


@login_required
def workout_set_create_view(request):
    return _set_form_view(request)


@login_required
def workout_set_update_view(request, pk):
    workout_set = get_object_or_404(WorkoutSet, pk=pk, workout__user=request.user)
    return _set_form_view(request, workout_set)


@login_required
@require_POST
def workout_set_delete_view(request, pk):
    workout_set = get_object_or_404(WorkoutSet, pk=pk, workout__user=request.user)
    workout_id = workout_set.workout_id
    workout_set.delete()
    messages.success(request, 'Set deleted.')
    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('workout_detail', pk=workout_id)
