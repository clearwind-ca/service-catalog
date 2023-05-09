import logging
import re

from django.conf import settings
from django.contrib.auth.middleware import AuthenticationMiddleware
from rest_framework.exceptions import AuthenticationFailed
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
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
        """
        Check to see if a login is required for this path.
        * True: a login will be required.
        * False: it won't.
        """
        # Avoid a circular import.
        from rest_framework.views import APIView

        user = request.user

        # If a user is authenticated, no login_required.
        if user.is_authenticated:
            return False

        # If the URL is in an IGNORE_PATH, no login_required.
        path = request.path
        if any(url.match(path) for url in IGNORE_PATHS):
            return False

        # If it's a 404, no login required.
        try:
            resolver = resolve(path)
        except Http404:
            return False

        # You can decorate class based views with login_required=False to skip this middleware.
        view_func = resolver.func
        if not getattr(view_func, "login_required", True):
            return False

        view_class = getattr(view_func, "view_class", None)
        if view_class and not getattr(view_class, "login_required", True):
            return False

        # If the resolver takes us to a view that is in the ignore list, no login required.
        if resolver.view_name in IGNORE_VIEW_NAMES:
            return False

        # See if this is DRF View Set and if so, let DRF Token Auth try to log the user in.
        # If they are logged in we are good and we can pass off to DRF to Authenticate them as needed.
        view_func_cls = getattr(view_func, "cls", None)
        if view_func_cls:
            auth_cls = getattr(view_func_cls, "authentication_classes", None)
            if auth_cls:
                # Let DRF handle the authentication
                drf_view = APIView()
                drf_request = drf_view.initialize_request(request)
                # Raises AuthenticationFailed if not successful
                try:
                    drf_request.user.is_authenticated
                except AuthenticationFailed:
                    # If we get here, the user is not authenticated.
                    request._is_drf = True
                    return True
                return False

        # If none of the above are met, we need the user to login.
        return True

    def check_orgs(self, request):
        # This should only be used in tests and not changed.
        if not settings.ENFORCE_ORG_MEMBERSHIP:
            return True

        # If the user is anonymous, they can't be in an org, so we can exit early.
        if request.user.is_anonymous:
            return False

        # Don't check on pages that are meant to be anonymous.
        resolver = resolve(request.path)
        if resolver.view_name in IGNORE_VIEW_NAMES:
            logger.info(f"Check-Orgs: Ignoring view name {resolver.view_name}")
            return True

        # First, something in the cache for this user?
        names = Organization.objects.values_list("name", flat=True)
        if not names:
            logger.error(f"Check-Orgs: No orgs found to check membership against.")
            return False

        # Include the org names in the key, so that if the orgs change we
        # end up with a stale result.
        key = f"orgs:{request.user.pk}:{','.join(names)}"
        result = cache.get(key)

        # If it's none there was nothing in the cache, so let's check True/False explicitly.
        if result in [True, False]:
            logger.error(f"Check-Orgs: Cache hit for {key} with {result}")
            return result

        # Next, check the database.
        valid = all([user.check_org_membership(request.user.username, name) for name in names])

        # Set a cache key for 5 minutes.
        cache.set(key, valid, 60 * 5)
        logger.error(f"Check-Orgs: Cache set for {key} with {valid}")
        return valid

    def process_request(self, request):
        request._is_drf = False
        login_required = self._login_required(request)

        # If the user is anonymous, but a login is not required, they are good.
        if request.user.is_anonymous and not login_required:
            return None  # Good, user can continue.

        # If user is authenticated, but we still don't need a login, they are good.
        if request.user.is_authenticated and not login_required:
            return None  # Good, user can continue.

        # If the user is authenticated, and a login is required, then we go check the orgs.
        if request.user.is_authenticated and login_required:
            if self.check_orgs(request):
                return None

        # This is a DRF request.
        if request._is_drf:
            # Return a non-HTML error response.
            # Ideally would be in the Accept format for the request.
            return HttpResponse("Sorry, nope", status=403)
        
        # Default, fail and redirect to the login-problem page.
        return redirect("web:login-problem")
