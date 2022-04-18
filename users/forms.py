from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from allauth.account.forms import LoginForm, SignupForm

class CustomUserCreationForm(UserCreationForm): # for admin
    class Meta:
        model = get_user_model()
        fields = ('email', 'username',)
        
class CustomUserChangeForm(UserChangeForm): # for admin
    class Meta:
        model = get_user_model()
        fields = ('email', 'username',)

class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'].widget.attrs.update({'autofocus': True})
    
    def login(self, *args, **kwargs):
        return super(CustomLoginForm, self).login(*args, **kwargs)
    
class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'autofocus': True})

    def save(self, request):

        # Ensure you call the parent class's save.
        # .save() returns a User object.
        user = super(CustomSignupForm, self).save(request)

        # Add your own processing here.

        # You must return the original result.
        return user
