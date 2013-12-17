from student.models import (User, UserProfile, Registration,
                            CourseEnrollmentAllowed, CourseEnrollment,
                            PendingEmailChange, UserStanding,
                            )
from course_modes.models import CourseMode
from django.contrib.auth.models import Group, AnonymousUser
from datetime import datetime
from factory import Factory, DjangoModelFactory, SubFactory, PostGenerationMethodCall, post_generation, Sequence
from uuid import uuid4
from pytz import UTC

# Factories don't have __init__ methods, and are self documenting
# pylint: disable=W0232


class GroupFactory(DjangoModelFactory):
    FACTORY_FOR = Group

    name = u'staff_MITx/999/Robot_Super_Course'

class UserStandingFactory(DjangoModelFactory):
    FACTORY_FOR = UserStanding

    user = None
    account_status = None
    changed_by = None


class UserProfileFactory(DjangoModelFactory):
    FACTORY_FOR = UserProfile

    user = None
    name = u'Robot Test'
    level_of_education = None
    gender = u'm'
    mailing_address = None
    goals = u'World domination'


class CourseModeFactory(DjangoModelFactory):
    FACTORY_FOR = CourseMode

    course_id = None
    mode_display_name = u'Honor Code',
    mode_slug = 'honor'
    min_price = 0
    suggested_prices = ''
    currency = 'usd'

class RegistrationFactory(DjangoModelFactory):
    FACTORY_FOR = Registration

    user = None
    activation_key = uuid4().hex.decode('ascii')


class UserFactory(DjangoModelFactory):
    FACTORY_FOR = User

    username = Sequence(u'robot{0}'.format)
    email = Sequence(u'robot+test+{0}@edx.org'.format)
    password = PostGenerationMethodCall('set_password',
                                        'test')
    first_name = Sequence(u'Robot{0}'.format)
    last_name = 'Test'
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = datetime(2012, 1, 1, tzinfo=UTC)
    date_joined = datetime(2011, 1, 1, tzinfo=UTC)

    @post_generation
    def profile(obj, create, extracted, **kwargs):
        if create:
            obj.save()
            return UserProfileFactory.create(user=obj, **kwargs)
        elif kwargs:
            raise Exception("Cannot build a user profile without saving the user")
        else:
            return None

    @post_generation
    def groups(self, create, extracted, **kwargs):
        if extracted is None:
            return

        if isinstance(extracted, basestring):
            extracted = [extracted]

        for group_name in extracted:
            self.groups.add(GroupFactory.simple_generate(create, name=group_name))


class NonRegisteredUserFactory(UserFactory):
    # only difference from UserFactory is the profile has nonregistered bit set
    @classmethod
    def _after_postgeneration(cls, obj, create, results=None):
        if create:
            obj.profile.nonregistered = True
            obj.profile.save()


class AnonymousUserFactory(Factory):
    FACTORY_FOR = AnonymousUser


class AdminFactory(UserFactory):
    is_staff = True


class CourseEnrollmentFactory(DjangoModelFactory):
    FACTORY_FOR = CourseEnrollment

    user = SubFactory(UserFactory)
    course_id = u'edX/toy/2012_Fall'


class CourseEnrollmentAllowedFactory(DjangoModelFactory):
    FACTORY_FOR = CourseEnrollmentAllowed

    email = 'test@edx.org'
    course_id = 'edX/test/2012_Fall'


class PendingEmailChangeFactory(DjangoModelFactory):
    """Factory for PendingEmailChange objects

    user: generated by UserFactory
    new_email: sequence of new+email+{}@edx.org
    activation_key: sequence of integers, padded to 30 characters
    """
    FACTORY_FOR = PendingEmailChange

    user = SubFactory(UserFactory)
    new_email = Sequence(u'new+email+{0}@edx.org'.format)
    activation_key = Sequence(u'{:0<30d}'.format)
