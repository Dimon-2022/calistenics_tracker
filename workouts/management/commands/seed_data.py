from django.core.management.base import BaseCommand
from workouts.models import Muscle, Exercise


class Command(BaseCommand):
    help = 'Seeds the database with initial muscle groups and exercises.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database with initial data...")

        # 1. Muscle groups (English)
        muscles_data = [
            'Chest',
            'Lats',
            'Upper Back / Traps',
            'Front Delts',
            'Side / Rear Delts',
            'Biceps',
            'Triceps',
            'Abs / Core',
            'Quads',
            'Glutes & Hamstrings',
            'Calves',
        ]

        muscles = {}
        for name in muscles_data:
            muscle_obj, _ = Muscle.objects.get_or_create(name=name)
            muscles[name] = muscle_obj

        # 2. Exercises (English)
        exercises_data = [
            {
                'name': 'Push-ups',
                'category': 'push',
                'description': 'Bodyweight exercise targeting chest, triceps, and shoulders.',
                'muscles': ['Chest', 'Triceps', 'Front Delts', 'Abs / Core']
            },
            {
                'name': 'Dips',
                'category': 'push',
                'description': 'Compound bodyweight movement for triceps and lower chest.',
                'muscles': ['Chest', 'Triceps', 'Front Delts']
            },
            {
                'name': 'Pull-ups',
                'category': 'pull',
                'description': 'Overhand pull exercise for upper back width and biceps.',
                'muscles': ['Lats', 'Upper Back / Traps', 'Biceps']
            },
            {
                'name': 'Chin-ups',
                'category': 'pull',
                'description': 'Underhand grip pull-up focusing more on biceps.',
                'muscles': ['Biceps', 'Lats']
            },
            {
                'name': 'Australian Pull-ups',
                'category': 'pull',
                'description': 'Horizontal bodyweight row for back thickness.',
                'muscles': ['Upper Back / Traps', 'Lats', 'Side / Rear Delts']
            },
            {
                'name': 'Hanging Leg Raises',
                'category': 'core',
                'description': 'Core strength exercise for lower abs and hip flexors.',
                'muscles': ['Abs / Core']
            },
            {
                'name': 'Plank',
                'category': 'core',
                'description': 'Isometric core stability hold.',
                'muscles': ['Abs / Core']
            },
            {
                'name': 'Squats',
                'category': 'push',
                'description': 'Fundamental bodyweight lower body movement.',
                'muscles': ['Quads', 'Glutes & Hamstrings']
            },
            {
                'name': 'Lunges',
                'category': 'push',
                'description': 'Unilateral leg exercise for quad strength and balance.',
                'muscles': ['Quads', 'Glutes & Hamstrings']
            },
            {
                'name': 'Wall Handstand Hold',
                'category': 'skill',
                'description': 'Calisthenics skill hold for shoulder stability.',
                'muscles': ['Front Delts', 'Side / Rear Delts', 'Triceps']
            },
        ]

        for ex_info in exercises_data:
            exercise, _ = Exercise.objects.get_or_create(
                name=ex_info['name'],
                defaults={
                    'category': ex_info['category'],
                    'description': ex_info['description']
                }
            )
            for m_name in ex_info['muscles']:
                if m_name in muscles:
                    exercise.target_muscles.add(muscles[m_name])

        self.stdout.write(self.style.SUCCESS("Database successfully seeded!"))