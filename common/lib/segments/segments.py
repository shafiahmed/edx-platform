"""
This module contains classes that represent segmentations of groups users.  This
is used e.g. for experiments that show different things to different students.

These classes are intended to be "simple" objects that are easily serializable to
json, so that they can be passed accross the network if needed.
"""

import json


class Group(object):
    """
    An id and name for a group of students.  The id should be unique
    within the CourseUserSegmentation this group appears in.
    """
    # in case we want to add to this class, a version will be handy
    # for deserializing old versions.  (This will be serialized in courses)
    VERSION = 1
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def to_json(self):
        """
        'Serialize' to a json-serializable representation.

        Returns:
            a dictionary with keys for the properties of the group.
        """
        return {"id": self.id,
                "name": self.name,
                "version": Group.VERSION}


    @staticmethod
    def from_json(value):
        """
        Deserialize a Group from a json-like representation.

        Args:
            value: a dictionary with keys for the properties of the group.

        Raises TypeError if the value doesn't have the right keys.
        """
        def check(key):
            if key not in value:
                raise TypeError("Group dict {0} missing value key '{1}'".format(
                    value, key))
        check("id")
        check("name")
        check("version")
        if value["version"] != Group.VERSION:
            raise TypeError("Group dict {0} has unexpected version".format(
                value))

        return Group(value["id"], value["name"])


class UserSegmentation(object):
    """
    A named way to segment users into groups, for any number of reasons.

    A segmentation may completely partition students in some group
    (e.g. everyone enrolled in a course), with each student in exactly one
    group, but it doesn't have to.  Some students may not be in any group in a
    segmentation, and some may be in multiple groups.

    There can be many types of segmentations, and some segmentations may have
    further invariants.  e.g. segmentations used for split testing will probably
    be partititions of students within a course, with each student being in
    exactly one group for an experiment.

    A Segmentation has an id, type, name, description, and a list of groups.
    The id is intended to be unique within a per-type context (e.g. for
    segmentations of users within a course, the ids should be unique per-course)

    Currently known segmentation types:
    'experiment': a segmentation used for testing of content.
        Intended for partitioning users in a course into non-overlapping groups.
    """
    VERSION = 1

    def __init__(self, id, segmentation_type, name, description, groups):

        self.id = id
        self.type = segmentation_type
        self.name = name
        self.description = description
        self.groups = groups


    def to_json(self):
        """
        'Serialize' to a json-serializable representation.

        Returns:
            a dictionary with keys for the properties of the segmentation.
        """
        return {"id": self.id,
                "type": self.type,
                "name": self.name,
                "description": self.description,
                "groups": [g.to_json() for g in self.groups],
                "version": UserSegmentation.VERSION}


    @staticmethod
    def from_json(value):
        """
        Deserialize a Group from a json-like representation.

        Args:
            value: a dictionary with keys for the properties of the group.

        Raises TypeError if the value doesn't have the right keys.
        """
        def check(key):
            if key not in value:
                raise TypeError("UserSegmentation dict {0} missing value key '{1}'"
                                .format(value, key))
        check("id")
        check("type")
        check("name")
        check("description")
        check("version")
        if value["version"] != UserSegmentation.VERSION:
            raise TypeError("UserSegmentation dict {0} has unexpected version"
                            .format(value))

        check("groups")
        groups = [Group.from_json(g) for g in value["groups"]]

        return UserSegmentation(value["id"],
                                      value["type"],
                                      value["name"],
                                      value["description"],
                                      groups)
