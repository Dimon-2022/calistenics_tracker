"""Progress analytics for the dashboard.

Buckets are computed in Python on local dates so the charts don't depend on
MySQL timezone tables (required by TruncDay/TruncMonth with USE_TZ=True).
"""
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta

from django.utils import timezone

from .models import Exercise, Workout, WorkoutSet

PERIODS = {
    'week': 'Week',
    'month': 'Month',
    'year': 'Year',
}


def _start_of_day(day):
    return timezone.make_aware(datetime.combine(day, time.min))


def _shift_months(day, months):
    month_index = day.year * 12 + day.month - 1 + months
    return date(month_index // 12, month_index % 12 + 1, 1)


def period_buckets(period, today=None):
    """Return (labels, bucket_starts, current_start, previous_start, end) for a period.

    week  -> last 7 days, one bucket per day
    month -> last 30 days, one bucket per day
    year  -> last 12 calendar months, one bucket per month
    """
    today = today or timezone.localdate()
    end = _start_of_day(today + timedelta(days=1))

    if period == 'year':
        first_month = _shift_months(today.replace(day=1), -11)
        starts = [_shift_months(first_month, i) for i in range(12)]
        labels = [d.strftime('%b %Y') for d in starts]
        current_start = _start_of_day(starts[0])
        previous_start = _start_of_day(_shift_months(first_month, -12))
    else:
        days = 7 if period == 'week' else 30
        starts = [today - timedelta(days=days - 1 - i) for i in range(days)]
        labels = [d.strftime('%a %d' if period == 'week' else '%b %d') for d in starts]
        current_start = _start_of_day(starts[0])
        previous_start = _start_of_day(starts[0] - timedelta(days=days))

    return labels, starts, current_start, previous_start, end


def pct_change(current, previous):
    """Percentage change, or None when there is nothing to compare against."""
    if not previous:
        return None
    # abs() keeps the sign meaningful for assisted (negative) weights
    return round((current - previous) / abs(previous) * 100, 1)


def _totals(sets, workout_ids):
    return {
        'workouts': len(workout_ids),
        'sets': len(sets),
        'reps': sum(s.reps or 0 for s in sets),
        'hold_seconds': int(sum(s.duration.total_seconds() for s in sets if s.duration)),
    }


def _best_by_exercise(sets):
    best = {}
    for s in sets:
        value = s.performance
        if value is None:
            continue
        if s.exercise_id not in best or value > best[s.exercise_id]:
            best[s.exercise_id] = value
    return best


def dashboard_stats(user, period='week', today=None):
    if period not in PERIODS:
        period = 'week'
    labels, starts, current_start, previous_start, end = period_buckets(period, today)

    sets = list(
        WorkoutSet.objects
        .filter(workout__user=user, workout__started_at__gte=previous_start, workout__started_at__lt=end)
        .select_related('exercise', 'workout')
    )
    current_sets = [s for s in sets if s.workout.started_at >= current_start]
    previous_sets = [s for s in sets if s.workout.started_at < current_start]

    workouts = Workout.objects.filter(user=user, started_at__gte=previous_start, started_at__lt=end)
    current_workout_ids = {w.id for w in workouts if w.started_at >= current_start}
    previous_workout_ids = {w.id for w in workouts if w.started_at < current_start}

    current = _totals(current_sets, current_workout_ids)
    previous = _totals(previous_sets, previous_workout_ids)
    changes = {key: pct_change(current[key], previous[key]) for key in current}

    # --- Chart series ---
    def bucket_index(moment):
        local_day = timezone.localdate(moment)
        if period == 'year':
            key = local_day.replace(day=1)
        else:
            key = local_day
        try:
            return starts.index(key)
        except ValueError:
            return None

    reps_series = [0] * len(starts)
    hold_series = [0] * len(starts)
    workout_series = [0] * len(starts)
    for s in current_sets:
        idx = bucket_index(s.workout.started_at)
        if idx is not None:
            reps_series[idx] += s.reps or 0
            hold_series[idx] += int(s.duration.total_seconds()) if s.duration else 0
    for w in workouts:
        if w.id in current_workout_ids:
            idx = bucket_index(w.started_at)
            if idx is not None:
                workout_series[idx] += 1

    # --- Top 3 most frequent exercises (by number of sets in the period) ---
    exercises = {s.exercise_id: s.exercise for s in sets}
    frequency = Counter(s.exercise_id for s in current_sets)
    top_frequent = [
        {'exercise': exercises[ex_id], 'sets': count}
        for ex_id, count in frequency.most_common(3)
    ]

    # --- Top 3 by progress: best set this period vs best set previous period ---
    best_now = _best_by_exercise(current_sets)
    best_before = _best_by_exercise(previous_sets)
    progress = []
    for ex_id, value in best_now.items():
        change = pct_change(value, best_before.get(ex_id))
        if change is not None:
            progress.append({
                'exercise': exercises[ex_id],
                'current': value,
                'previous': best_before[ex_id],
                'pct': change,
            })
    progress.sort(key=lambda item: item['pct'], reverse=True)

    # --- Muscle group distribution (sets per muscle) for the period ---
    muscle_counts = defaultdict(int)
    exercise_muscles = {
        ex.id: [m.name for m in ex.target_muscles.all()]
        for ex in Exercise.objects.filter(id__in=frequency.keys()).prefetch_related('target_muscles')
    }
    for ex_id, count in frequency.items():
        for name in exercise_muscles.get(ex_id, []):
            muscle_counts[name] += count
    muscles = sorted(muscle_counts.items(), key=lambda item: item[1], reverse=True)

    return {
        'period': period,
        'period_label': PERIODS[period],
        'periods': PERIODS,
        'current': current,
        'previous': previous,
        'changes': changes,
        'top_frequent': top_frequent,
        'top_progress': progress[:3],
        'chart': {
            'labels': labels,
            'reps': reps_series,
            'hold': hold_series,
            'workouts': workout_series,
            'muscles': {'labels': [m[0] for m in muscles], 'values': [m[1] for m in muscles]},
        },
    }
