import logging

from django.contrib.auth.models import User
from django.db import models

log = logging.getLogger(__name__)


class CourseUserSegmentationGroup(models.Model):
    """
    This model represents the groups of users for different user segmentations
    in a course.

    User segmentations can have different types, which may be treated specially.
    For example, a user can be in at most one experimental group per user
    segmentation with type experiment.  These sorts of constraints must be
    enforced by the code that uses each type of segmentation, since having a
    single table for different segmentation types makes it impossible to apply
    constraints in the DB.
    """

    user = models.ForeignKey(User, db_index=True,
                                   related_name='course_segmentation_groups',
                                   help_text="Who is in this group?")

    course_id = models.CharField(max_length=255, db_index=True,
                                 help_text="Which course is this group associated with?")

    segmentation_type = models.CharField(max_length=32)

    segmentation_id = models.IntegerField(
        help_text="What is the segmentation_id of this group?")

    group_id = models.IntegerField(
        help_text="What is the group_id of this group, within its segmentation?")
