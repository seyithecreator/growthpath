from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Recommendation


@login_required
def recommendation_list(request):
    recs = Recommendation.objects.filter(user=request.user).order_by('rank')
    return render(request, 'recommendations/list.html', {'recs': recs})
