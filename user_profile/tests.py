from catalog.tests import BaseTestCase
from django.urls import reverse
from user_profile.models import Profile
from oauthlogin.models import OAuthConnection
from unittest.mock import Mock, patch

class TestUserProfile(BaseTestCase):

    @patch("user_profile.models.user")
    def test_profile_created(self, mock_user):
        with self.settings(GITHUB_IGNORE_PROFILE=False):
            profile = Mock()
            profile.avatar_url = 'https://example.com/avatar.png'
            mock_user.login_as_user.return_value.get_user.return_value = profile
            OAuthConnection.objects.create(user=self.user, access_token="1234")
            self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_change_profile(self):
        self.assertEquals(Profile.objects.get(user=self.user).timezone, "UTC")
        url = reverse("profile:profile-update")
        self.client.force_login(user=self.user)
        res = self.client.post(url, {"timezone": "Africa/Abidjan"})
        self.assertEquals(Profile.objects.get(user=self.user).timezone, "Africa/Abidjan")