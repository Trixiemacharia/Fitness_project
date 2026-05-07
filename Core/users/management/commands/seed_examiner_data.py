from datetime import date, timedelta
from decimal import Decimal
import random
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import BaseCommand, CommandError, call_command
from django.db import transaction
from django.utils import timezone

from exercises.models import Category, Exercise, ExerciseLog
from nutrition.models import FoodItem, MealLog
from users.models import Feedback, ProgressLog, UserPreferences, UserProfile, WeightLog


class Command(BaseCommand):
    help = "Seed examiner/demo data into the local database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Load fixtures even when records already exist and refresh demo users/logs.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options['force']

        if force:
            self._clear_demo_data()

        self._ensure_reference_data(force=force)
        summary = self._seed_demo_users()

        self.stdout.write(self.style.SUCCESS(
            "Examiner seed complete: "
            f"{summary['users']} users, "
            f"{summary['exercise_logs']} exercise logs, "
            f"{summary['meal_logs']} meal logs, "
            f"{summary['feedback']} feedback entries."
        ))

    def _ensure_reference_data(self, force=False):
        exercises_fixture = Path(settings.BASE_DIR) / 'exercises' / 'fixtures' / 'my_fixture.json'
        foods_fixture = Path(settings.BASE_DIR) / 'nutrition' / 'fixtures' / 'kenyan_foods_fixture.json'

        if force or not Category.objects.exists():
            call_command('loaddata', str(exercises_fixture), verbosity=0)
        if force or not FoodItem.objects.exists():
            call_command('loaddata', str(foods_fixture), verbosity=0)

    def _clear_demo_data(self):
        demo_usernames = ['examiner_admin', 'demo_member', 'demo_trainer', 'demo_beginner']
        demo_users = User.objects.filter(username__in=demo_usernames)

        Feedback.objects.filter(user__in=demo_users).delete()
        ProgressLog.objects.filter(user__in=demo_users).delete()
        WeightLog.objects.filter(user__in=demo_users).delete()
        MealLog.objects.filter(user__in=demo_users).delete()
        ExerciseLog.objects.filter(user__in=demo_users).delete()
        UserPreferences.objects.filter(user__in=demo_users).delete()
        UserProfile.objects.filter(user__in=demo_users).delete()
        demo_users.delete()

    def _seed_demo_users(self):
        today = date.today()
        exercises = list(Exercise.objects.order_by('id')[:12])
        foods = list(FoodItem.objects.order_by('id')[:12])

        if not exercises:
            raise CommandError("No exercises found after loading fixtures.")
        if not foods:
            raise CommandError("No food items found after loading fixtures.")

        demo_specs = [
            {
                'username': 'examiner_admin',
                'password': 'admin1234',
                'email': 'admin@fittrack.demo',
                'is_staff': True,
                'is_superuser': True,
                'name': 'Examiner Admin',
                'gender': 'F',
                'height': 168,
                'goal_type': 'tone',
                'activity_level': 'active',
                'fitness_level': 'advanced',
                'prefered_focus': ['abs', 'arms', 'glutes'],
                'meal_plan_recommendations': 'Yes',
                'wants_meal_plan': True,
                'fitness_goal': 'stay_active',
                'preferred_days': ['mon', 'wed', 'fri'],
                'joined_offset': 120,
            },
            {
                'username': 'demo_member',
                'password': 'demo1234',
                'email': 'member@fittrack.demo',
                'is_staff': False,
                'is_superuser': False,
                'name': 'Demo Member',
                'gender': 'M',
                'height': 175,
                'goal_type': 'bulk',
                'activity_level': 'moderate',
                'fitness_level': 'intermediate',
                'prefered_focus': ['arms', 'back', 'shoulder'],
                'meal_plan_recommendations': 'Yes',
                'wants_meal_plan': True,
                'fitness_goal': 'build_muscle',
                'preferred_days': ['mon', 'thu', 'sat'],
                'joined_offset': 45,
            },
            {
                'username': 'demo_trainer',
                'password': 'demo1234',
                'email': 'trainer@fittrack.demo',
                'is_staff': False,
                'is_superuser': False,
                'name': 'Demo Trainer',
                'gender': 'F',
                'height': 162,
                'goal_type': 'tone',
                'activity_level': 'very_active',
                'fitness_level': 'advanced',
                'prefered_focus': ['legs', 'glutes', 'abs'],
                'meal_plan_recommendations': 'No',
                'wants_meal_plan': False,
                'fitness_goal': 'improve_endurance',
                'preferred_days': ['tue', 'thu', 'sun'],
                'joined_offset': 15,
            },
            {
                'username': 'demo_beginner',
                'password': 'demo1234',
                'email': 'beginner@fittrack.demo',
                'is_staff': False,
                'is_superuser': False,
                'name': 'Demo Beginner',
                'gender': 'M',
                'height': 181,
                'goal_type': 'lose_weight',
                'activity_level': 'light',
                'fitness_level': 'beginner',
                'prefered_focus': ['legs', 'abs'],
                'meal_plan_recommendations': 'Yes',
                'wants_meal_plan': True,
                'fitness_goal': 'lose_weight',
                'preferred_days': ['wed', 'fri'],
                'joined_offset': 4,
            },
        ]

        summary = {
            'users': 0,
            'exercise_logs': 0,
            'meal_logs': 0,
            'feedback': 0,
        }

        for index, spec in enumerate(demo_specs):
            user, created = User.objects.get_or_create(
                username=spec['username'],
                defaults={
                    'email': spec['email'],
                    'is_staff': spec['is_staff'],
                    'is_superuser': spec['is_superuser'],
                },
            )
            user.email = spec['email']
            user.is_staff = spec['is_staff']
            user.is_superuser = spec['is_superuser']
            user.set_password(spec['password'])
            joined_at = timezone.now() - timedelta(days=spec['joined_offset'])
            user.date_joined = joined_at
            user.save()

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'name': spec['name'],
                    'email': spec['email'],
                    'password_hash': user.password,
                    'gender': spec['gender'],
                    'date_of_birth': date(1998 + index, 6, 15),
                    'height': spec['height'],
                    'goal_type': spec['goal_type'],
                    'activity_level': spec['activity_level'],
                    'fitness_level': spec['fitness_level'],
                    'prefered_focus': spec['prefered_focus'],
                    'meal_plan_recommendations': spec['meal_plan_recommendations'],
                    'wants_meal_plan': spec['wants_meal_plan'],
                    'bio': f"{spec['name']} seeded for examiner review.",
                },
            )

            UserPreferences.objects.update_or_create(
                user=user,
                defaults={
                    'fitness_goal': spec['fitness_goal'],
                    'preferred_days': spec['preferred_days'],
                    'units': 'metric',
                    'dark_mode': False,
                    'notifications': True,
                },
            )

            WeightLog.objects.get_or_create(
                user=user,
                date=today - timedelta(days=7),
                defaults={
                    'weight': Decimal(str(70 + index * 4)),
                    'unit': 'kg',
                    'note': 'Seeded baseline weight',
                },
            )

            summary['users'] += 1
            summary['exercise_logs'] += self._seed_exercise_logs(user, exercises, today, index)
            summary['meal_logs'] += self._seed_meal_logs(user, foods, today, index)
            summary['feedback'] += self._seed_feedback(user, index)

        return summary

    def _seed_exercise_logs(self, user, exercises, today, seed_offset):
        random.seed(f"fittrack-exercises-{user.username}")
        created_count = 0
        selected = exercises[seed_offset:seed_offset + 4] or exercises[:4]

        for position, exercise in enumerate(selected):
            sets_completed = min(exercise.get_sets(), max(1, exercise.get_sets() - (position % 2)))
            log, created = ExerciseLog.objects.get_or_create(
                user=user,
                exercise=exercise,
                defaults={'sets_completed': sets_completed},
            )
            if not created:
                log.sets_completed = sets_completed
                log.save(update_fields=['sets_completed', 'updated_at'])
            created_count += 1 if created else 0

        for day_offset in range(5):
            ProgressLog.objects.update_or_create(
                user=user,
                date=today - timedelta(days=day_offset),
                defaults={
                    'calories_burned': 250 + seed_offset * 40 + day_offset * 20,
                    'workout_done': day_offset != 3,
                    'steps': 4500 + seed_offset * 800 + day_offset * 350,
                    'water_intake': 5 + ((seed_offset + day_offset) % 4),
                },
            )

        return created_count

    def _seed_meal_logs(self, user, foods, today, seed_offset):
        created_count = 0
        meal_types = ['breakfast', 'lunch', 'dinner']

        for day_offset in range(3):
            for meal_index, meal_type in enumerate(meal_types):
                food = foods[(seed_offset + day_offset + meal_index) % len(foods)]
                log, created = MealLog.objects.get_or_create(
                    user=user,
                    food_item=food,
                    date=today - timedelta(days=day_offset),
                    meal_type=meal_type,
                    defaults={
                        'portion_size': 120 + (meal_index * 30),
                        'notes': 'Seeded meal log',
                    },
                )
                if not created:
                    log.portion_size = 120 + (meal_index * 30)
                    log.notes = 'Seeded meal log'
                    log.save()
                created_count += 1 if created else 0

        return created_count

    def _seed_feedback(self, user, index):
        if user.is_staff:
            return 0

        feedback_items = [
            ('feature', 'It would help to export a weekly progress summary.'),
            ('bug', 'The dashboard should keep my selected workout filter after refresh.'),
            ('complaint', 'Some exercise descriptions could use simpler beginner wording.'),
        ]

        created_count = 0
        category, message = feedback_items[index - 1]
        entry, created = Feedback.objects.get_or_create(
            user=user,
            category=category,
            message=message,
            defaults={
                'status': 'in_review' if category != 'complaint' else 'new',
                'admin_response': 'Thanks, this was seeded for examiner review.' if category == 'feature' else '',
            },
        )
        if not created:
            entry.status = 'in_review' if category != 'complaint' else 'new'
            if category == 'feature':
                entry.admin_response = 'Thanks, this was seeded for examiner review.'
            entry.save()
        created_count += 1 if created else 0
        return created_count
