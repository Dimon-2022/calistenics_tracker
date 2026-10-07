from datetime import date, datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import WorkoutForm
from .models import Exercise, Muscle, Workout, WorkoutSet
from .stats import dashboard_stats, pct_change


def aware(day, hour=10):
    return timezone.make_aware(datetime.combine(day, datetime.min.time()) + timedelta(hours=hour))


class BaseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('athlete', password='pass12345!')
        self.other = User.objects.create_user('other', password='pass12345!')
        self.chest = Muscle.objects.create(name='Chest')
        self.pushups = Exercise.objects.create(name='Push-ups', category='push')
        self.plank = Exercise.objects.create(name='Plank', category='core', metric_type=Exercise.METRIC_TIME)
        self.pushups.target_muscles.add(self.chest)
        self.client.login(username='athlete', password='pass12345!')


class AuthTests(TestCase):
    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_signup_logs_user_in(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newbie', 'email': '', 'password1': 'Str0ng-pass!', 'password2': 'Str0ng-pass!',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(User.objects.filter(username='newbie').exists())


class ExerciseTests(BaseTestCase):
    def test_create_custom_exercise(self):
        response = self.client.post(reverse('exercise_create'), {
            'name': 'Archer Push-ups', 'category': 'push', 'metric_type': 'reps', 'target_muscles': [self.chest.pk],
        })
        self.assertRedirects(response, reverse('exercise_list'))
        exercise = Exercise.objects.get(name='Archer Push-ups')
        self.assertEqual(exercise.user, self.user)
        self.assertEqual(list(exercise.target_muscles.all()), [self.chest])

    def test_duplicate_name_rejected(self):
        response = self.client.post(reverse('exercise_create'), {
            'name': 'push-ups', 'category': 'push', 'metric_type': 'reps',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Exercise.objects.filter(user=self.user).exists())

    def test_other_users_custom_exercises_hidden(self):
        Exercise.objects.create(name='Secret Move', category='skill', user=self.other)
        response = self.client.get(reverse('exercise_list'))
        self.assertNotContains(response, 'Secret Move')

    def test_cannot_edit_global_exercise(self):
        response = self.client.get(reverse('exercise_update', args=[self.pushups.pk]))
        self.assertEqual(response.status_code, 404)

    def test_filter_by_muscle(self):
        response = self.client.get(reverse('exercise_list'), {'target_muscles': [self.chest.pk]})
        self.assertEqual(list(response.context['exercises']), [self.pushups])


class WorkoutTests(BaseTestCase):
    def formset_data(self, rows, **workout):
        data = {
            'started_at': '2026-10-01T10:00',
            'finished_at': '2026-10-01T11:00',
            'type': 'volume',
            'notes': '',
            'sets-TOTAL_FORMS': str(len(rows)),
            'sets-INITIAL_FORMS': '0',
            'sets-MIN_NUM_FORMS': '1',
            'sets-MAX_NUM_FORMS': '1000',
        }
        data.update(workout)
        for i, row in enumerate(rows):
            for key, value in row.items():
                data[f'sets-{i}-{key}'] = value
        return data

    def test_create_workout_with_sets_numbers_them(self):
        data = self.formset_data([
            {'exercise': self.pushups.pk, 'reps': '20', 'rest_time': '90'},
            {'exercise': self.pushups.pk, 'reps': '18', 'rest_time': '90'},
            {'exercise': self.plank.pk, 'duration': '60', 'rest_time': '60'},
        ])
        response = self.client.post(reverse('workout_create'), data)
        workout = Workout.objects.get(user=self.user)
        self.assertRedirects(response, reverse('workout_detail', args=[workout.pk]))
        numbers = list(workout.sets.filter(exercise=self.pushups).values_list('set_number', flat=True))
        self.assertEqual(numbers, [1, 2])
        self.assertEqual(workout.sets.get(exercise=self.plank).set_number, 1)

    def test_finished_before_started_is_invalid(self):
        form = WorkoutForm(data={
            'started_at': '2026-10-01T10:00', 'finished_at': '2026-10-01T09:00', 'type': 'volume',
        })
        self.assertFalse(form.is_valid())

    def test_cannot_log_other_users_custom_exercise(self):
        foreign = Exercise.objects.create(name='Foreign', category='push', user=self.other)
        response = self.client.post(reverse('workout_create'), self.formset_data([
            {'exercise': foreign.pk, 'reps': '10', 'rest_time': '60'},
        ]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Workout.objects.exists())

    def test_hold_exercise_requires_duration(self):
        response = self.client.post(reverse('workout_create'), self.formset_data([
            {'exercise': self.plank.pk, 'reps': '1', 'rest_time': '60'},
        ]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Workout.objects.exists())

    def test_other_users_workout_is_404(self):
        workout = Workout.objects.create(user=self.other, type='volume')
        self.assertEqual(self.client.get(reverse('workout_detail', args=[workout.pk])).status_code, 404)

    def test_detail_groups_sets(self):
        workout = Workout.objects.create(user=self.user, type='volume')
        WorkoutSet.objects.create(workout=workout, exercise=self.pushups, reps=10)
        WorkoutSet.objects.create(workout=workout, exercise=self.pushups, reps=12)
        response = self.client.get(reverse('workout_detail', args=[workout.pk]))
        self.assertContains(response, '2 sets · 22 reps')
        self.assertContains(response, 'Chest')

    def test_exercise_used_in_history_cannot_be_deleted(self):
        custom = Exercise.objects.create(name='Mine', category='push', user=self.user)
        workout = Workout.objects.create(user=self.user, type='volume')
        WorkoutSet.objects.create(workout=workout, exercise=custom, reps=5)
        self.client.post(reverse('exercise_delete', args=[custom.pk]))
        self.assertTrue(Exercise.objects.filter(pk=custom.pk).exists())


class WorkoutSetTests(BaseTestCase):
    def test_compose_set_for_own_workout(self):
        workout = Workout.objects.create(user=self.user, type='strength')
        response = self.client.post(reverse('workout_set_create'), {
            'workout': workout.pk, 'exercise': self.pushups.pk, 'reps': '15', 'rest_time': '00:02:00', 'rpe': '8',
        })
        self.assertRedirects(response, reverse('workout_detail', args=[workout.pk]))
        workout_set = workout.sets.get()
        self.assertEqual((workout_set.set_number, workout_set.rpe), (1, 8))

    def test_cannot_add_set_to_foreign_workout(self):
        workout = Workout.objects.create(user=self.other, type='strength')
        response = self.client.post(reverse('workout_set_create'), {
            'workout': workout.pk, 'exercise': self.pushups.pk, 'reps': '15', 'rest_time': '60',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(WorkoutSet.objects.exists())

    def test_list_only_shows_own_sets(self):
        mine = Workout.objects.create(user=self.user, type='volume')
        theirs = Workout.objects.create(user=self.other, type='volume')
        WorkoutSet.objects.create(workout=mine, exercise=self.pushups, reps=11)
        WorkoutSet.objects.create(workout=theirs, exercise=self.pushups, reps=99)
        response = self.client.get(reverse('workout_set_list'))
        self.assertContains(response, '11 reps')
        self.assertNotContains(response, '99 reps')


class StatsTests(BaseTestCase):
    def log(self, day, exercise, **set_fields):
        workout = Workout.objects.create(user=self.user, type='volume', started_at=aware(day))
        return WorkoutSet.objects.create(workout=workout, exercise=exercise, **set_fields)

    def test_pct_change(self):
        self.assertEqual(pct_change(15, 10), 50.0)
        self.assertIsNone(pct_change(5, 0))
        self.assertEqual(pct_change(-5, -10), 50.0)

    def test_week_progress_and_top_exercises(self):
        today = date(2026, 10, 8)
        self.log(today - timedelta(days=10), self.pushups, reps=20)
        self.log(today - timedelta(days=9), self.plank, duration=timedelta(seconds=60))
        self.log(today - timedelta(days=1), self.pushups, reps=25)
        self.log(today, self.pushups, reps=22)
        self.log(today, self.plank, duration=timedelta(seconds=90))

        stats = dashboard_stats(self.user, 'week', today=today)

        self.assertEqual(stats['current']['workouts'], 3)
        self.assertEqual(stats['current']['reps'], 47)
        self.assertEqual(stats['changes']['reps'], 135.0)
        self.assertEqual(stats['chart']['reps'][-1], 22)
        self.assertEqual(stats['top_frequent'][0]['exercise'], self.pushups)
        progress = {item['exercise'].name: item['pct'] for item in stats['top_progress']}
        self.assertEqual(progress, {'Plank': 50.0, 'Push-ups': 25.0})
        self.assertEqual(stats['top_progress'][0]['exercise'], self.plank)

    def test_year_buckets_by_month(self):
        today = date(2026, 10, 8)
        self.log(date(2026, 3, 15), self.pushups, reps=30)
        stats = dashboard_stats(self.user, 'year', today=today)
        self.assertEqual(len(stats['chart']['labels']), 12)
        self.assertEqual(stats['chart']['labels'][0], 'Nov 2025')
        self.assertEqual(stats['chart']['reps'][4], 30)

    def test_dashboard_renders(self):
        self.log(timezone.localdate(), self.pushups, reps=10)
        for period in ('week', 'month', 'year', 'bogus'):
            response = self.client.get(reverse('dashboard'), {'period': period})
            self.assertEqual(response.status_code, 200)
