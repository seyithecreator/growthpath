from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .engine import PriorityEngine


@login_required
def priority_list(request):
    engine = PriorityEngine(request.user)
    items = engine.rank_goals()
    return render(request, 'priorities/list.html', {'items': items})
