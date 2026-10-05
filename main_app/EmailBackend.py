from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailBackend(ModelBackend):
    def authenticate(self, request=None, username=None, password=None, **kwargs):
        user_model = get_user_model()
        email = (username or kwargs.get(user_model.USERNAME_FIELD) or "").strip().lower()
        if not email or password is None:
            return None
        try:
            user = user_model.objects.get(email__iexact=email)
        except user_model.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
