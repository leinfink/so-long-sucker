from allauth.account.views import LoginView, LogoutView, SignupView

from config.utils import get_base_template

class CustomLoginView(LoginView):
    def get_context_data(self, **kwargs):
        context = super(CustomLoginView, self).get_context_data(**kwargs)
        context['base_template'] = get_base_template(self.request)
        return context
    
class CustomLogoutView(LogoutView):
    def get_context_data(self, **kwargs):
        context = super(CustomLogoutView, self).get_context_data(**kwargs)
        context['base_template'] = get_base_template(self.request)
        return context
    
class CustomSignupView(SignupView):
    def get_context_data(self, **kwargs):
        context = super(CustomSignupView, self).get_context_data(**kwargs)
        context['base_template'] = get_base_template(self.request)
        return context
