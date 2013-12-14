"""
This module contains classes that represent segmentations of groups users.  This
is used e.g. for experiments that show different things to different students.

These classes are intended to be "simple" objects that are easily serializable to
json, so that they can be passed accross the network if needed.
"""

import logging

from .models import CourseUserSegmentationGroup

log = logging.getLogger(__name__)


def get_user_segmentation_groups(course_id, user_segmentation, user_id):
    """
    Given a course_id, a UserSegmentation, and a user_id, return the user's
    groups in that segmentation, if they have any.

    Args:
        course_id: string in the format 'org/course/run'
        user_segmentation: a segments.UserSegmentation.
        user_id: The id of a django User object.

    Returns:
        A list of group_ids if the user already has groups for this
        segmentation.  Will be empty if there are none.
    """

    records = CourseUserSegmentationGroup.objects.filter(
        course_id=course_id,
        segmentation_type=user_segmentation.type,
        segmentation_id=user_segmentation.id,
        user__id=user_id)

    return [record.group_id for record in records]


def save_user_segmentation_group(course_id, user_segmentation, user_id,
                                 group_id):
    """
    Save a record of user being in group_id for a particular user_segmentation
    in course_id.

    Args:
        course_id: string in the format 'org/course/run'
        user_segmentation: a segments.UserSegmentation.
        user_id: The id of a django User object.

    Returns a bool that's True if a new record was created, and False otherwise.
    """

    # impl note: this sets the foreign key field directly to avoid an extra query
    # to look up the User object needed for a standard create(user=a_user_object, ...)
    # (http://stackoverflow.com/questions/2846029/django-set-foreign-key-using-integer)
    entry, created = CourseUserSegmentationGroup.objects.get_or_create(
        user_id=user_id,
        course_id=course_id,
        segmentation_type=user_segmentation.type,
        segmentation_id=user_segmentation.id,
        group_id=group_id,)

    return created
