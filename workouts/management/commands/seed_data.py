from django.core.management.base import BaseCommand
from workouts.models import Muscle, Exercise


# Names used by earlier versions of this seed — renamed in place so history is kept.
LEGACY_NAMES = {
    'Віджимання від підлоги (Push-ups)': 'Push-ups',
    'Віджимання на брусах (Dips)': 'Dips',
    'Підтягування прямим хватом (Pull-ups)': 'Pull-ups',
    'Підтягування зворотним хватом (Chin-ups)': 'Chin-ups',
    'Австралійські підтягування (Australian Pull-ups)': 'Australian Pull-ups',
    'Підйом ніг у висі (Hanging Leg Raises)': 'Hanging Leg Raises',
    'Планка (Plank)': 'Plank',
    'Присідання (Squats)': 'Squats',
    'Випади (Lunges)': 'Lunges',
    'Сійка на руках біля стіни (Handstand Hold)': 'Wall Handstand Hold',
}


class Command(BaseCommand):
    help = 'Seeds the database with initial muscle groups and exercises.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database with initial data...")

        # 1. Muscle groups
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

        # 2. Global exercises
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
                'name': 'Pike Push-ups',
                'category': 'push',
                'description': 'Hips high push-up variation that shifts the load to the shoulders.',
                'muscles': ['Front Delts', 'Triceps']
            },
            {
                'name': 'Weighted Dips',
                'category': 'push',
                'metric_type': 'weighted',
                'description': 'Dips with a belt or vest; progress is tracked by added weight.',
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
                'name': 'Weighted Pull-ups',
                'category': 'pull',
                'metric_type': 'weighted',
                'description': 'Pull-ups with added weight; progress is tracked by added weight.',
                'muscles': ['Lats', 'Upper Back / Traps', 'Biceps']
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
                'metric_type': 'time',
                'description': 'Isometric core stability hold.',
                'muscles': ['Abs / Core']
            },
            {
                'name': 'L-sit',
                'category': 'core',
                'metric_type': 'time',
                'description': 'Static hold on parallettes or floor with legs extended forward.',
                'muscles': ['Abs / Core', 'Triceps']
            },
            {
                'name': 'Squats',
                'category': 'legs',
                'description': 'Fundamental bodyweight lower body movement.',
                'muscles': ['Quads', 'Glutes & Hamstrings']
            },
            {
                'name': 'Lunges',
                'category': 'legs',
                'description': 'Unilateral leg exercise for quad strength and balance.',
                'muscles': ['Quads', 'Glutes & Hamstrings']
            },
            {
                'name': 'Pistol Squats',
                'category': 'legs',
                'description': 'Single-leg squat requiring strength, balance and mobility.',
                'muscles': ['Quads', 'Glutes & Hamstrings']
            },
            {
                'name': 'Calf Raises',
                'category': 'legs',
                'description': 'Standing raises on the toes, ideally from a step.',
                'muscles': ['Calves']
            },
            {
                'name': 'Wall Handstand Hold',
                'category': 'skill',
                'metric_type': 'time',
                'description': 'Calisthenics skill hold for shoulder stability.',
                'muscles': ['Front Delts', 'Side / Rear Delts', 'Triceps']
            },
            {
                'name': 'Muscle-ups',
                'category': 'skill',
                'description': 'Explosive pull-up transitioning into a dip above the bar.',
                'muscles': ['Lats', 'Chest', 'Triceps', 'Biceps']
            },
        ]

        for old_name, new_name in LEGACY_NAMES.items():
            Exercise.objects.filter(user__isnull=True, name=old_name).update(name=new_name)

        for ex_info in exercises_data:
            exercise, _ = Exercise.objects.update_or_create(
                user=None,
                name=ex_info['name'],
                defaults={
                    'category': ex_info['category'],
                    'metric_type': ex_info.get('metric_type', Exercise.METRIC_REPS),
                    'description': ex_info['description'],
                }
            )
            exercise.target_muscles.set([muscles[m_name] for m_name in ex_info['muscles']])

        self.stdout.write(self.style.SUCCESS("Database successfully seeded!"))
