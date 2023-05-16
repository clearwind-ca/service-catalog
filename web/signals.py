import logging

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in
from django.contrib.contenttypes.models import ContentType

from gh.user import check_org_membership
from services.models import Organization

logger = logging.getLogger(__name__)


def user_logged_in_handler(sender, request, user, **kwargs):
    names = Organization.objects.values_list("name", flat=True)
    if not names:
        logger.info(f"No orgs found to check membership against")
        return False

    username = user.username
    is_member = all([check_org_membership(username, name) for name in names])
    members_user_set = Group.objects.get(name="members").user_set
    public_user_set = Group.objects.get(name="public").user_set

    if is_member:
        if not members_user_set.filter(username=username).exists():
            members_user_set.add(user)
            logger.info(f"Added user {username} to group members")

    if not is_member:
        if members_user_set.filter(username=username).exists():
            members_user_set.remove(user)
            logger.info(f"Removed user {user.username} from group members")

        if settings.ALLOW_PUBLIC_READ_ACCESS:
            if not public_user_set.filter(username=username).exists():
                public_user_set.add(user)
                logger.info(f"Added user {username} to group public")

        elif public_user_set.filter(username=username).exists():
            public_user_set.remove(user)
            logger.info(f"Removed user {username} from group public")


user_logged_in.connect(user_logged_in_handler)
