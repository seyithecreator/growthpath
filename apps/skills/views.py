import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UserSkill


@login_required
def skill_list(request):
    skills = UserSkill.objects.filter(
        user=request.user, is_active=True
    ).select_related('domain').prefetch_related('history')

    skills_data = []
    for skill in skills:
        history = list(skill.history.order_by('recorded_at'))
        skills_data.append({
            'skill': skill,
            'history_labels': json.dumps([h.recorded_at.strftime('%d %b') for h in history]),
            'history_scores': json.dumps([h.score for h in history]),
        })

    return render(request, 'skills/list.html', {
        'skills_data': skills_data,
        'active_nav': 'skills',
    })
