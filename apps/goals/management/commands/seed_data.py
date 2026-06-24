"""
Management command: python manage.py seed_data
Seeds the database with sample data for Nigerian university student testing.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
import random
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds sample data for GrowthPath development and testing'

    NIGERIAN_UNIVERSITIES = [
        'University of Lagos', 'Obafemi Awolowo University',
        'University of Ibadan', 'Ahmadu Bello University',
        'University of Nigeria Nsukka', 'Covenant University',
        'Lagos State University', 'Federal University of Technology Akure',
    ]

    SAMPLE_USERS = [
        {'first_name': 'Tunde', 'last_name': 'Adeyemi', 'username': 'tunde_a', 'email': 'tunde@test.com'},
        {'first_name': 'Chioma', 'last_name': 'Okafor', 'username': 'chioma_o', 'email': 'chioma@test.com'},
        {'first_name': 'Emeka', 'last_name': 'Nwosu', 'username': 'emeka_n', 'email': 'emeka@test.com'},
        {'first_name': 'Fatima', 'last_name': 'Bello', 'username': 'fatima_b', 'email': 'fatima@test.com'},
        {'first_name': 'Seun', 'last_name': 'Ogunleye', 'username': 'seun_o', 'email': 'seun@test.com'},
    ]

    GOALS_TEMPLATES = [
        {'title': 'Complete Python Certification', 'category': 'technical', 'priority': 'high',
         'metric': 'Pass final exam with 80%+'},
        {'title': 'Final Year Research Paper', 'category': 'academic', 'priority': 'high',
         'metric': 'Submit 5000-word paper'},
        {'title': 'Daily Exercise Routine', 'category': 'health', 'priority': 'medium',
         'metric': '30min exercise for 60 days'},
        {'title': 'Leadership Development', 'category': 'career', 'priority': 'medium',
         'metric': 'Complete leadership programme'},
        {'title': 'Personal Finance Management', 'category': 'personal', 'priority': 'low',
         'metric': 'Save ₦50,000 per month'},
        {'title': 'Machine Learning Fundamentals', 'category': 'technical', 'priority': 'high',
         'metric': 'Complete 10 ML projects'},
        {'title': 'Public Speaking Skills', 'category': 'career', 'priority': 'medium',
         'metric': 'Deliver 5 presentations'},
    ]

    SKILL_DOMAINS = [
        ('Python Programming', 'technical', 'ti-brand-python', '#2563EB'),
        ('Data Analysis', 'technical', 'ti-chart-bar', '#7C3AED'),
        ('Academic Writing', 'academic', 'ti-file-text', '#D97706'),
        ('Communication', 'soft_skills', 'ti-message-circle', '#16A34A'),
        ('Time Management', 'soft_skills', 'ti-clock', '#0891B2'),
        ('Research Skills', 'academic', 'ti-search', '#7C3AED'),
        ('Leadership', 'leadership', 'ti-users', '#D97706'),
        ('Critical Thinking', 'academic', 'ti-brain', '#DC2626'),
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('🌱 Seeding GrowthPath data...'))

        self._seed_skill_domains()
        self._seed_users()
        self._seed_goals_and_activities()

        self.stdout.write(self.style.SUCCESS('✅ Seeding complete!'))

    def _seed_skill_domains(self):
        from apps.skills.models import SkillDomain
        for name, domain_type, icon, color in self.SKILL_DOMAINS:
            SkillDomain.objects.get_or_create(
                name=name,
                defaults={'domain_type': domain_type, 'icon': icon,
                          'color_hex': color, 'is_global': True}
            )
        self.stdout.write(f'  • Created {len(self.SKILL_DOMAINS)} skill domains')

    def _seed_users(self):
        from apps.skills.models import SkillDomain, UserSkill, SkillScoreHistory

        for data in self.SAMPLE_USERS:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'university': random.choice(self.NIGERIAN_UNIVERSITIES),
                    'department': random.choice(['Computer Science', 'Engineering', 'Business Admin']),
                    'year_of_study': random.randint(2, 5),
                    'streak_days': random.randint(0, 30),
                    'total_points': random.randint(100, 2000),
                    'ai_personalisation': True,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()

            # Seed skills
            for domain in SkillDomain.objects.filter(is_global=True):
                skill, _ = UserSkill.objects.get_or_create(
                    user=user, domain=domain,
                    defaults={
                        'current_score': round(random.uniform(40, 85), 1),
                        'target_score': round(random.uniform(75, 95), 1),
                    }
                )
                # Add 6 weeks of history (skip if already seeded)
                if not skill.history.exists():
                    base = skill.current_score - random.uniform(10, 25)
                    for week in range(6):
                        score = round(base + (week * random.uniform(1.5, 4)), 1)
                        SkillScoreHistory.objects.create(
                            skill=skill,
                            score=score,
                            delta=round(random.uniform(0, 4), 1),
                        )

        self.stdout.write(f'  • Created {len(self.SAMPLE_USERS)} users with skills')

    def _seed_goals_and_activities(self):
        from apps.goals.models import Goal, Milestone
        from apps.activities.models import ActivityLog, ProductivitySnapshot

        today = date.today()
        activity_types = ['study', 'reading', 'project', 'assessment', 'workshop']

        for user in User.objects.filter(username__in=[u['username'] for u in self.SAMPLE_USERS]):
            # Create goals
            for i, tmpl in enumerate(random.sample(self.GOALS_TEMPLATES, 4)):
                goal, _ = Goal.objects.get_or_create(
                    user=user,
                    title=tmpl['title'],
                    defaults={
                        'category': tmpl['category'],
                        'priority': tmpl['priority'],
                        'success_metric': tmpl['metric'],
                        'target_value': 100.0,
                        'current_value': round(random.uniform(10, 85), 1),
                        'start_date': today - timedelta(days=random.randint(14, 60)),
                        'target_date': today + timedelta(days=random.randint(7, 90)),
                        'status': 'active',
                    }
                )
                # Milestones
                for j in range(random.randint(2, 4)):
                    Milestone.objects.get_or_create(
                        goal=goal, order=j+1,
                        defaults={
                            'title': f'Milestone {j+1}',
                            'target_date': goal.start_date + timedelta(days=(j+1)*14),
                            'is_completed': random.choice([True, False]),
                        }
                    )

            # Activity logs (last 14 days)
            for day_offset in range(14):
                log_date = today - timedelta(days=day_offset)
                if random.random() < 0.75:   # 75% chance of activity each day
                    for _ in range(random.randint(1, 3)):
                        start_hour = random.randint(6, 21)
                        started = timezone.make_aware(
                            timezone.datetime(log_date.year, log_date.month, log_date.day,
                                             start_hour, random.randint(0, 59))
                        )
                        duration = random.randint(20, 180)
                        ActivityLog.objects.create(
                            user=user,
                            activity_type=random.choice(activity_types),
                            title=f"{random.choice(['Study', 'Practice', 'Review', 'Work on'])} session",
                            started_at=started,
                            ended_at=started + timedelta(minutes=duration),
                            duration_minutes=duration,
                            productivity_score=random.randint(2, 5),
                            focus_level=random.randint(2, 5),
                            goal_progress_delta=round(random.uniform(0, 5), 1),
                        )

                    # Daily snapshot
                    avg_prod = round(random.uniform(2.5, 4.8), 2)
                    ProductivitySnapshot.objects.get_or_create(
                        user=user, date=log_date,
                        defaults={
                            'total_sessions': random.randint(1, 4),
                            'total_minutes': random.randint(40, 300),
                            'avg_productivity': avg_prod,
                            'avg_focus': round(random.uniform(2.5, 4.5), 2),
                            'goals_advanced': random.randint(0, 3),
                            'skills_practised': random.randint(0, 2),
                        }
                    )

        self.stdout.write('  • Goals, milestones, and activity logs created')
