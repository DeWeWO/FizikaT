from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from .models import TelegramSession

User = get_user_model()

class TelegramAuthBackend(BaseBackend):
    """Telegram session token orqali authentication"""
    
    def authenticate(self, request, telegram_token=None, **kwargs):
        if telegram_token:
            try:
                session = TelegramSession.objects.get(session_token=telegram_token)
                return session.user
            except TelegramSession.DoesNotExist:
                return None
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None