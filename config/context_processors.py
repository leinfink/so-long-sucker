from django.conf import settings

def hosting_settings(request):
    return {'SSL_WEBSOCKETS': settings.SSL_WEBSOCKETS}
