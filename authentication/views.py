from django.shortcuts import render, redirect
from .forms import LoginForm, SignUpForm, UserProfileForm
from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.conf import settings

LOGGED_IN_REDIRECT = settings.LOGGED_IN_REDIRECT


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data.get("password1"))
            new_user.save()
            messages.success(request, "User registered successfully!")
            return redirect("login")
        else:
            for value in form.errors.values():
                messages.error(request, f"{value}")

    if request.user.is_authenticated:
        return redirect(LOGGED_IN_REDIRECT)

    form = SignUpForm()
    context = {"form": form}
    return render(request, "new_authentication/register.html", context)


def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            identifier = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")

            if User.objects.filter(email=identifier).exists():
                username = (
                    User.objects.filter(email=identifier)
                    .values_list("username", flat=True)
                    .get()
                )
                user = auth.authenticate(request, username=username, password=password)
            else:
                user = auth.authenticate(
                    request, username=identifier, password=password
                )

            if user is not None:
                auth.login(request, user)
                return redirect(LOGGED_IN_REDIRECT)
            else:
                messages.error(
                    request,
                    "Incorrect username/email or password! Verify and try again.",
                )
                return redirect("login")

    if request.user.is_authenticated:
        return redirect(LOGGED_IN_REDIRECT)

    form = LoginForm()
    context = {"form": form}
    return render(request, "new_authentication/login.html", context)


def logout(request):
    auth.logout(request)
    return redirect("login")


# logged in user
@login_required(login_url="/login")
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            auth.update_session_auth_hash(request, user)
            messages.success(request, "Your password was succesfully updated!")
            return redirect(LOGGED_IN_REDIRECT)
        else:
            messages.error(request, "Ops, an error ocurred! Please, try again :)")

    form = PasswordChangeForm(request.user)
    context = {"form": form}
    return render(request, "user/change_password.html", context)


@login_required(login_url="/login")
def update_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = UserProfileForm(
            request.POST, request.FILES, instance=profile, user=request.user
        )
        if form.is_valid():
            user = request.user
            user.username = form.cleaned_data.get("username")
            user.email = form.cleaned_data.get("email")
            user.first_name = form.cleaned_data.get("first_name")
            user.last_name = form.cleaned_data.get("last_name")
            user.save()
            if request.POST.get("avatar_remove"):
                if profile.profile_image:
                    profile.profile_image.delete(save=False)
                profile.profile_image = None

            form.save()
            return redirect("update_profile")
    else:
        form = UserProfileForm(instance=profile, user=request.user)
    return render(request, "temp/profile.html", {"form": form})
