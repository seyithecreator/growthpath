from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect('goals:dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to GrowthPath, {user.display_name}!')
            return redirect('goals:dashboard')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})
