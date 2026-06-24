"""
apps/goals/roadmap.py
Template-based milestone generator. Produces a contextual roadmap of
milestones for a goal based on its category and title keywords.
No external LLM API needed — upgrading to one later is straightforward.
"""

from datetime import timedelta

MILESTONE_TEMPLATES = {
    'academic': [
        ('Define your research question and scope', 'Write a clear, focused question that guides your entire project.'),
        ('Complete a literature review', 'Read and summarise at least 10 relevant sources on your topic.'),
        ('Build your study/research plan', 'Break your workload into weekly tasks with specific deadlines.'),
        ('Complete first draft or first exam attempt', 'Produce a full first draft or sit a practice exam.'),
        ('Get feedback and revise', 'Share work with a lecturer, peer, or study group and incorporate feedback.'),
        ('Final review and polishing', 'Proofread, check citations, and ensure all requirements are met.'),
        ('Submit / sit the final assessment', 'Submit your work or attend the exam with confidence.'),
    ],
    'technical': [
        ('Set up your development environment', 'Install all tools, IDEs, and dependencies needed for the project.'),
        ('Complete a beginner tutorial or course module', 'Follow a structured intro to build foundational understanding.'),
        ('Build your first small project or prototype', 'Apply what you have learned to a mini real-world task.'),
        ('Study core concepts in depth', 'Go beyond tutorials — read documentation and understand the "why".'),
        ('Complete a medium-complexity project', 'Build something that demonstrates practical skill (e.g. an app, script, model).'),
        ('Seek code review or peer feedback', 'Have someone review your code or project and implement improvements.'),
        ('Document and publish your work', 'Write a README, push to GitHub, or share on LinkedIn/portfolio.'),
        ('Sit a certification or assessment', 'Validate your skills with a formal test, certification, or technical interview.'),
    ],
    'career': [
        ('Define your target role and industry', 'Research 3–5 specific job titles and companies you want to work at.'),
        ('Update your CV and LinkedIn profile', 'Tailor them to the roles you are targeting; get a peer review.'),
        ('Build or update your portfolio', 'Add recent projects, case studies, or writing samples.'),
        ('Network — attend events or reach out to professionals', 'Connect with at least 5 people in your field this month.'),
        ('Apply to 10 positions or opportunities', 'Send tailored applications and track responses.'),
        ('Prepare for interviews', 'Practise common questions, research companies, and prepare stories.'),
        ('Evaluate offers and make a decision', 'Compare opportunities against your long-term goals.'),
    ],
    'personal': [
        ('Define what success looks like specifically', 'Write a concrete description of the outcome you want.'),
        ('Identify the habits or routines needed', 'List the daily or weekly actions that will get you there.'),
        ('Start with a 7-day trial', 'Commit to the new habit for 7 days without pressure.'),
        ('Review progress at the 2-week mark', 'Reflect honestly on what is and is not working.'),
        ('Overcome the first major obstacle', 'Identify the biggest barrier and create a plan to address it.'),
        ('Reach the halfway milestone', 'Celebrate hitting 50% and re-evaluate the plan for the second half.'),
        ('Achieve your goal', 'Complete the final action that makes you say "I did it."'),
    ],
    'health': [
        ('Get a baseline measurement', 'Record your current metrics (weight, resting heart rate, times, etc.).'),
        ('Consult a professional if needed', 'See a doctor, trainer, or nutritionist to set safe targets.'),
        ('Set up your environment for success', 'Prepare your space, buy needed equipment, or prep healthy meals.'),
        ('Complete your first week consistently', 'Follow your routine every day for 7 days straight.'),
        ('Reach the 30-day consistency mark', 'Maintain your habit for a full month — a major milestone.'),
        ('Measure progress against baseline', 'Compare your current metrics to where you started.'),
        ('Achieve the final health target', 'Hit the specific number or outcome you set at the start.'),
    ],
    'financial': [
        ('Audit your current income and expenses', 'Track every naira in and out for two weeks.'),
        ('Set a realistic budget', 'Create a monthly budget with specific category limits.'),
        ('Identify and cut one major unnecessary expense', 'Find the biggest money leak and plug it.'),
        ('Open a dedicated savings account or fund', 'Separate your savings from your spending money.'),
        ('Reach 25% of your financial target', 'First quarter milestone — proof the plan works.'),
        ('Reach 50% of your financial target', 'Halfway point — review and adjust if needed.'),
        ('Achieve the full financial target', 'Hit your savings, debt payoff, or investment goal.'),
    ],
}

KEYWORD_OVERRIDES = {
    'research': 'academic',
    'thesis': 'academic',
    'exam': 'academic',
    'dissertation': 'academic',
    'project': 'technical',
    'code': 'technical',
    'build': 'technical',
    'develop': 'technical',
    'app': 'technical',
    'programming': 'technical',
    'python': 'technical',
    'data': 'technical',
    'job': 'career',
    'internship': 'career',
    'career': 'career',
    'cv': 'career',
    'interview': 'career',
    'linkedin': 'career',
    'fitness': 'health',
    'workout': 'health',
    'exercise': 'health',
    'weight': 'health',
    'run': 'health',
    'diet': 'health',
    'saving': 'financial',
    'money': 'financial',
    'investment': 'financial',
    'debt': 'financial',
    'budget': 'financial',
}


class RoadmapGenerator:
    def __init__(self, goal):
        self.goal = goal

    def _pick_category(self):
        title_lower = self.goal.title.lower()
        for keyword, cat in KEYWORD_OVERRIDES.items():
            if keyword in title_lower:
                return cat
        return self.goal.category if self.goal.category in MILESTONE_TEMPLATES else 'personal'

    def generate(self):
        """
        Returns a list of dicts: {title, description, order, target_date}.
        target_dates are spread evenly across the goal's timeline.
        """
        category = self._pick_category()
        templates = MILESTONE_TEMPLATES[category]

        start = self.goal.start_date
        end = self.goal.target_date
        total_days = (end - start).days
        n = len(templates)

        milestones = []
        for i, (title, description) in enumerate(templates, start=1):
            fraction = i / n
            target_date = start + timedelta(days=int(total_days * fraction))
            milestones.append({
                'title': title,
                'description': description,
                'order': i,
                'target_date': target_date,
            })
        return milestones
