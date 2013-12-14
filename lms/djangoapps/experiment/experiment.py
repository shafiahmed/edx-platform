"""
This is the 'service-like' API to the experiments app.  It may at some point be
exposed via http views, but for now is just an in-process interface.
"""

from segments import UserSegmentation, Group
from xmodule.modulestore.django import modulestore


def get_condition_for_user(course_id, user_segmentation_id, user_id):
    """
    If the user is already assigned to a condition for experiment_id, return the
    condition_id.

    If not, assign them to one of the conditions, persist that decision, and
    return the condition_id.

    If the condition they are assigned to doesn't exist anymore, re-assign to one of
    the existing conditions and return its id.
    """
    course = modulestore().get_course(course_id)
    user_segmentation = _get_user_segmentation_for_experiment(course,
                                                              user_segmentation_id)
    if user_segmentation is None:
        raise ValueError(
            "Configuration problem!  No user_segmentation with id {0} and "
            "type experiment in course {1}".format(user_segmentation_id, course_id))

    group = _get_group(user_id, user_segmentation)

    return group.id


def _get_user_segmentation_for_experiment(course, user_segmentation_id):
    """
    Look for a user segmentation with a matching id and type 'experiment'
    in the course.

    Returns:
        A UserSegmentation, or None if not found.
    """
    for segmentation in course.user_segmentations:
        if segmentation.type == 'experiment' and segmentation.id == user_segmentation_id:
            return segmentation

    return None


def _get_group(user_id, user_segmentation):
    """
    Return the group of user_id in user_segmentation.  If they don't already
    have one assigned, pick one and save it.
    """
    # TODO: implement properly
    return user_segmentation.groups[-1]
