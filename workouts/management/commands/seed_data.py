from django.core.management.base import BaseCommand
from workouts.models import Muscle, Exercise


class Command(BaseCommand):
    help = 'Заповнює базу даних початковим списком м\'язів та вправ'

    def handle(self, *args, **kwargs):
        self.stdout.write("Починаємо заповнення бази даних...")

        # 1. Створюємо основні м'язи
        muscles_data = [
            'Грудні м\'язи (Chest)',
            'Широкі м\'язи спини (Lats)',
            'Верх спини / Трапеції',
            'Передні дельти (Front Delts)',
            'Середні / Задні дельти (Side/Rear Delts)',
            'Біцепс (Biceps)',
            'Трицепс (Triceps)',
            'Прес / Кор (Abs/Core)',
            'Квадрицепс (Quads)',
            'Сідниці та біцепс стегна (Glutes/Hamstrings)',
            'Ікри (Calves)',
        ]

        muscles = {}
        for name in muscles_data:
            muscle_obj, created = Muscle.objects.get_or_create(name=name)
            muscles[name] = muscle_obj

        self.stdout.write(self.style.SUCCESS(f"Успішно створено м'язів: {len(muscles)}"))

        # 2. Створюємо базові калістенічні / силові вправи
        exercises_data = [
            {
                'name': 'Віджимання від підлоги (Push-ups)',
                'category': 'push',
                'description': 'Базова вправа для грудей, трицепсів та плечей.',
                'muscles': [
                    'Грудні м\'язи (Chest)',
                    'Трицепс (Triceps)',
                    'Передні дельти (Front Delts)',
                    'Прес / Кор (Abs/Core)'
                ]
            },
            {
                'name': 'Віджимання на брусах (Dips)',
                'category': 'push',
                'description': 'Силова вправа з власною вагою на трицепс та груди.',
                'muscles': [
                    'Грудні м\'язи (Chest)',
                    'Трицепс (Triceps)',
                    'Передні дельти (Front Delts)'
                ]
            },
            {
                'name': 'Підтягування прямим хватом (Pull-ups)',
                'category': 'pull',
                'description': 'Основна вправа для розвитку ширини спини та біцепса.',
                'muscles': [
                    'Широкі м\'язи спини (Lats)',
                    'Верх спини / Трапеції',
                    'Біцепс (Biceps)'
                ]
            },
            {
                'name': 'Підтягування зворотним хватом (Chin-ups)',
                'category': 'pull',
                'description': 'Акцентована вправа на біцепс та нижню частину спини.',
                'muscles': [
                    'Біцепс (Biceps)',
                    'Широкі м\'язи спини (Lats)'
                ]
            },
            {
                'name': 'Австралійські підтягування (Australian Pull-ups)',
                'category': 'pull',
                'description': 'Горизонтальні тяги для розвитку товщини спини.',
                'muscles': [
                    'Верх спини / Трапеції',
                    'Широкі м\'язи спини (Lats)',
                    'Задні дельти (Side/Rear Delts)'
                ]
            },
            {
                'name': 'Підйом ніг у висі (Hanging Leg Raises)',
                'category': 'core',
                'description': 'Вправа для зміцнення нижнього преса та згиначів стегна.',
                'muscles': [
                    'Прес / Кор (Abs/Core)'
                ]
            },
            {
                'name': 'Планка (Plank)',
                'category': 'core',
                'description': 'Статична вправа на зміцнення м\'язів кору.',
                'muscles': [
                    'Прес / Кор (Abs/Core)'
                ]
            },
            {
                'name': 'Присідання (Squats)',
                'category': 'push',
                'description': 'Базова вправа для розвитку ніг.',
                'muscles': [
                    'Квадрицепс (Quads)',
                    'Сідниці та біцепс стегна (Glutes/Hamstrings)'
                ]
            },
            {
                'name': 'Випади (Lunges)',
                'category': 'push',
                'description': 'Однонога вправа для ніг та балансу.',
                'muscles': [
                    'Квадрицепс (Quads)',
                    'Сідниці та біцепс стегна (Glutes/Hamstrings)'
                ]
            },
            {
                'name': 'Сійка на руках біля стіни (Handstand Hold)',
                'category': 'skill',
                'description': 'Елемент калістеніки для плечей та балансу.',
                'muscles': [
                    'Передні дельти (Front Delts)',
                    'Середні / Задні дельти (Side/Rear Delts)',
                    'Трицепс (Triceps)'
                ]
            },
        ]

        for ex_info in exercises_data:
            exercise, created = Exercise.objects.get_or_create(
                name=ex_info['name'],
                defaults={
                    'category': ex_info['category'],
                    'description': ex_info['description']
                }
            )

            for m_name in ex_info['muscles']:
                if m_name in muscles:
                    exercise.target_muscles.add(muscles[m_name])

        self.stdout.write(self.style.SUCCESS(f"Успішно додано вправ: {len(exercises_data)}"))
        self.stdout.write(self.style.SUCCESS("База даних успішно засіяна!"))