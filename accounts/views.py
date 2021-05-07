from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth import *
from .forms import RegistrationForm
from django.contrib.auth.models import User
from app.models import Profile
from django.contrib import messages

def get_ip(request):

    address = request.META.get('HTTP_X_FORWARDED_FOR')

    if address:
        ip = address.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip


def registration_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password1"]
            User.objects.create_user(username=username, password=password, email=email)
            user = authenticate(username=username, password=password)
            Profile.objects.create(user=user)
            login(request, user)
            return HttpResponseRedirect("/")
    else:
        form = RegistrationForm()
    context = {"form": form}
    return render(request, "accounts/registration.html", context)

def login_view(request):

    if request.user.is_authenticated:
        return HttpResponseRedirect('/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # user_profile = Profile.objects.filter(user=user)
            # user_profile(get_ip(request))
            # user_profile.save()

            return HttpResponseRedirect("/")

        else:
            messages.info(request, 'Username OR Password not correct.')

    context = {}
    return render(request, 'accounts/login.html')