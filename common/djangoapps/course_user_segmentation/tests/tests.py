import django.test
from django.contrib.auth.models import User
from django.conf import settings

from django.test.utils import override_settings

from course_groups.models import CourseUserGroup
from course_groups.cohorts import (get_cohort, get_course_cohorts,
                                   is_commentable_cohorted, get_cohort_by_name)

from xmodule.modulestore.django import modulestore, clear_existing_modulestores

from xmodule.modulestore.tests.django_utils import mixed_store_config

# NOTE: running this with the lms.envs.test config works without
# manually overriding the modulestore.  However, running with
# cms.envs.test doesn't.

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_MAPPING = {'edX/toy/2012_Fall': 'xml'}
TEST_DATA_MIXED_MODULESTORE = mixed_store_config(TEST_DATA_DIR, TEST_MAPPING)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestUserSegmentations(django.test.TestCase):
    pass
