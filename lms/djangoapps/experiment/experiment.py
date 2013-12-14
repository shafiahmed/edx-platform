"""
This is the 'service-like' API to the experiments app.  It may at some point be
exposed via http views, but for now is just an in-process interface.
"""

import random


from xmodule.segments.segments import UserSegmentation, Group
from xmodule.modulestore.django import modulestore

from course_user_segmentation import segmentation


# tl;dr: global state is bad.  capa reseeds random every time a problem is loaded.  Even
# if and when that's fixed, it's a good idea to have a local generator to avoid any other
# code that messes with the global random module.
_local_random = None

def local_random():
    """
    Get the local random number generator.  In a function so that we don't run
    random.Random() at import time.
    """
    # ironic, isn't it?
    global _local_random

    if _local_random is None:
        _local_random = random.Random()

    return _local_random



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

    group_id = _get_group(course_id, user_segmentation, user_id)

    return group_id


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


def _get_group(course_id, user_segmentation, user_id):
    """
    Return the group of user_id in user_segmentation.  If they don't already
    have one assigned, pick one and save it.
    """

    group_ids = segmentation.get_user_segmentation_groups(
        course_id, user_segmentation, user_id)

    if len(group_ids) > 1:
        raise ValueError(
            "Found more than one experimental group for user_id {0}, user_segmentation_id"
            " {1}, course {2}"
            .format(user_id, user_segmentation.id, course_id))

    if len(group_ids) == 1:
        # TODO: check whether this id is valid.  If not, create a new one.
        return group_ids[0]

    # TODO: what's the atomicity of the get above and the save here?
    # If it's not in a single transaction, we could get a situation where
    # the user ends up in two groups--low probability, but still bad.
    # (If it is truly atomic, we should be fine--if one process is in the
    # process of finding no group and making one, the other should block till it
    # appears.  HOWEVER, if we allow reads by the second one while the first
    # process runs the transaction, we have a problem again: could read empty,
    # have the first transaction finish, and pick a different group in a
    # different process.)

    # TODO: emit analytics event!
    
    # otherwise, we need to pick one, save it, then return it
    group = local_random().choice(user_segmentation.groups)
    created = segmentation.save_user_segmentation_group(
        course_id, user_segmentation, user_id, group.id)

    # just for extra safety, make sure we did in fact create the element
    if not created:
        raise ValueError("Oops.  Invariant not true--we already had user {0}"
                         " in group {1} for segmentation {2} in course {3}"
                         .format(user_id, group.id, user_segmentation.id, course_id))

    return group.id

