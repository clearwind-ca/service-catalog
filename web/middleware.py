import logging
import re

from django.conf import settings
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.views import redirect_to_login
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import redirect
from django.urls import resolve

from gh import user
from services.models import Organization

logger = logging.getLogger(__name__)

IGNORE_PATHS = [re.compile(url) for url in settings.LOGIN_REQUIRED_IGNORE_PATHS]
IGNORE_VIEW_NAMES = list(settings.LOGIN_REQUIRED_IGNORE_VIEW_NAMES)
REDIRECT_FIELD_NAME = settings.LOGIN_REQUIRED_REDIRECT_FIELD_NAME

# See https://github.com/CleitonDeLima/django-login-required-middleware/blob/master/login_required/middleware.py for the
# source of this, with the changes to add in DRF.


class CatalogMiddleware(AuthenticationMiddleware):
    def _login_required(self, request):
        # Avoid a circular import.
        user = request.user
        from rest_framework.views import APIView

        if user.is_authenticated:
            return user

        path = request.path
        if any(url.match(path) for url in IGNORE_PATHS):
            return user

        try:
            resolver = resolve(path)
        except Http404:
            return redirect("web:login-problem")

        view_func = resolver.func

        if not getattr(view_func, "login_required", True):
            return user

        view_class = getattr(view_func, "view_class", None)
        if view_class and not getattr(view_class, "login_required", True):
            return user

        if resolver.view_name in IGNORE_VIEW_NAMES:
            return user

        # See if this is DRF View Set
        view_func_cls = getattr(view_func, "cls", None)
        if view_func_cls:
            auth_cls = getattr(view_func_cls, "authentication_classes", None)
            if auth_cls:
                # Let DRF handle the authentication
                drf_view = APIView()
                drf_request = drf_view.initialize_request(request)
                # Raises AuthenticationFailed if not successful
                drf_request.user.is_authenticated
                return drf_request.user

        return redirect("web:login-problem")

    def check_orgs(self, request):
        if request.user.is_anonymous:
            return False

        # Don't check on pages that are meant to be anonymous.
        resolver = resolve(request.path)
        if resolver.view_name in IGNORE_VIEW_NAMES:
            logger.info(f"Check-Orgs: Ignoring view name {resolver.view_name}")
            return True

        # First, something in the cache for this user?
        names = Organization.objects.values_list("name", flat=True)
        # Include the org names in the key, so that if the orgs change we
        # end up with a stale result.
        key = f"orgs:{request.user.pk}:{','.join(names)}"
        result = cache.get(key)
        # If it's none there was nothing in the cache.
        if result in [True, False]:
            logger.error(f"Check-Orgs: Cache hit for {key} with {result}")
            return result

        # Next, check the database.
        valid = all([user.check_org_membership(request.user.username, name) for name in names])
        cache.set(key, valid, 60 * 5)  # 5 minutes
        logger.error(f"Check-Orgs: Cache set for {key} with {valid}")
        return valid

    def process_request(self, request):
        res = self._login_required(request)
        if isinstance(res, type(request.user)):
            if request.user.is_anonymous:
                return None

            # Validate that the user is a member of the organization.
            if self.check_orgs(request):
                return None

            return redirect("web:login-problem")
        return res
