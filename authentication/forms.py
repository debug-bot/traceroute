from django import forms
from django.contrib.auth.models import User
from .snippets import verify_password
from .models import UserProfile


class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Repeat Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email"]
        password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
        password2 = forms.CharField(label="Repeat Password", widget=forms.PasswordInput)

    def clean(self):
        username = self.cleaned_data.get("username")
        email = self.cleaned_data.get("email")
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        error_list = dict()

        verify_password(
            field_name="password1",
            password1=password1,
            password2=password2,
            error_list=error_list,
        )

        if User.objects.filter(email=email).exists():
            error_list["email"] = "Email already registered!"

        if User.objects.filter(username=username).exists():
            error_list["username"] = "Username already registered!"

        if error_list is not None:
            for error in error_list:
                error_message = error_list[error]
                self.add_error(error, error_message)

        return self.cleaned_data


class LoginForm(forms.Form):
    email = forms.CharField(label="Email or Username", required=True)
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput, required=True
    )


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(label="Old Password", widget=forms.PasswordInput)
    password1 = forms.CharField(label="Set Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)


class UserProfileForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg form-control-solid",
                "placeholder": "Username",
            }
        ),
        label="Username",
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control form-control-lg form-control-solid",
                "placeholder": "Email",
            }
        ),
        label="Email",
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg form-control-solid mb-3 mb-lg-0",
                "placeholder": "First Name",
            }
        ),
        label="First Name",
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg form-control-solid",
                "placeholder": "Last Name",
            }
        ),
        label="Last Name",
    )

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "profile_image",
            "bio",
            "phone",
            "location",
        ]
        widgets = {
            "profile_image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Profile Image",
                }
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control form-control-lg form-control-solid",
                    "rows": 4,
                    "placeholder": "Tell us about yourself",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg form-control-solid",
                    "placeholder": "Phone Number",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg form-control-solid",
                    "placeholder": "Location",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)  # Get the user instance passed to the form
        super().__init__(*args, **kwargs)
        if user:
            self.fields["username"].initial = user.username
            self.fields["email"].initial = user.email
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if (
            User.objects.filter(username=username)
            .exclude(pk=self.instance.user.pk)
            .exists()
        ):
            raise forms.ValidationError("This username is already taken.")
        return username
