"""
Unit tests for the asset upload endpoint.
"""

#pylint: disable=C0111
#pylint: disable=W0621
#pylint: disable=W0212

from datetime import datetime, timedelta
from io import BytesIO
from pytz import UTC
import json
import re
from unittest import TestCase, skip
from .utils import CourseTestCase
from contentstore.views import assets
from xmodule.contentstore.content import StaticContent, XASSET_LOCATION_TAG
from xmodule.modulestore import Location
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore.mongo.base import location_to_query


class AssetsTestCase(CourseTestCase):
    def setUp(self):
        super(AssetsTestCase, self).setUp()
        location = loc_mapper().translate_location(self.course.location.course_id, self.course.location, False, True)
        self.url = location.url_reverse('assets/', '')

    def test_basic(self):
        resp = self.client.get(self.url, HTTP_ACCEPT='text/html')
        self.assertEquals(resp.status_code, 200)

    def test_static_url_generation(self):
        location = Location(['i4x', 'foo', 'bar', 'asset', 'my_file_name.jpg'])
        path = StaticContent.get_static_path_from_location(location)
        self.assertEquals(path, '/static/my_file_name.jpg')


class AssetsToyCourseTestCase(CourseTestCase):
    """
    Tests the assets returned from assets_handler for the toy test course.
    """
    def test_toy_assets(self):
        module_store = modulestore('direct')
        _, course_items = import_from_xml(
            module_store,
            'common/test/data/',
            ['toy'],
            static_content_store=contentstore(),
            verbose=True
        )
        course = course_items[0]
        location = loc_mapper().translate_location(course.location.course_id, course.location, False, True)
        url = location.url_reverse('assets/', '')

        resp = self.client.get(url, HTTP_ACCEPT='application/json')
        jsonResponse = json.loads(resp.content)
        assets = jsonResponse['assets']
        self.assertEquals(jsonResponse['start'], 0)
        self.assertEquals(jsonResponse['totalCount'], 3)
        self.assertEquals(len(assets), 3)

        resp = self.client.get(url + "?page_size=2", HTTP_ACCEPT='application/json')
        jsonResponse = json.loads(resp.content)
        assets = jsonResponse['assets']
        self.assertEquals(jsonResponse['start'], 0)
        self.assertEquals(jsonResponse['totalCount'], 3)
        self.assertEquals(len(assets), 2)

        resp = self.client.get(url + "?page_size=2&page=1", HTTP_ACCEPT='application/json')
        jsonResponse = json.loads(resp.content)
        assets = jsonResponse['assets']
        self.assertEquals(jsonResponse['start'], 2)
        self.assertEquals(jsonResponse['totalCount'], 3)
        self.assertEquals(len(assets), 1)


class UploadTestCase(CourseTestCase):
    """
    Unit tests for uploading a file
    """
    def setUp(self):
        super(UploadTestCase, self).setUp()
        location = loc_mapper().translate_location(self.course.location.course_id, self.course.location, False, True)
        self.url = location.url_reverse('assets/', '')

    @skip("CorruptGridFile error on continuous integration server")
    def test_happy_path(self):
        f = BytesIO("sample content")
        f.name = "sample.txt"
        resp = self.client.post(self.url, {"name": "my-name", "file": f})
        self.assertEquals(resp.status_code, 200)

    def test_no_file(self):
        resp = self.client.post(self.url, {"name": "file.txt"}, "application/json")
        self.assertEquals(resp.status_code, 400)


class AssetToJsonTestCase(TestCase):
    """
    Unit test for transforming asset information into something
    we can send out to the client via JSON.
    """
    def test_basic(self):
        upload_date = datetime(2013, 6, 1, 10, 30, tzinfo=UTC)

        location = Location(['i4x', 'foo', 'bar', 'asset', 'my_file_name.jpg'])
        thumbnail_location = Location(['i4x', 'foo', 'bar', 'asset', 'my_file_name_thumb.jpg'])

        output = assets._get_asset_json("my_file", upload_date, location, thumbnail_location, True)

        self.assertEquals(output["display_name"], "my_file")
        self.assertEquals(output["date_added"], "Jun 01, 2013 at 10:30 UTC")
        self.assertEquals(output["url"], "/i4x/foo/bar/asset/my_file_name.jpg")
        self.assertEquals(output["portable_url"], "/static/my_file_name.jpg")
        self.assertEquals(output["thumbnail"], "/i4x/foo/bar/asset/my_file_name_thumb.jpg")
        self.assertEquals(output["id"], output["url"])
        self.assertEquals(output['locked'], True)

        output = assets._get_asset_json("name", upload_date, location, None, False)
        self.assertIsNone(output["thumbnail"])


class LockAssetTestCase(CourseTestCase):
    """
    Unit test for locking and unlocking an asset.
    """

    def test_locking(self):
        """
        Tests a simple locking and unlocking of an asset in the toy course.
        """
        def verify_asset_locked_state(locked):
            """ Helper method to verify lock state in the contentstore """
            asset_location = StaticContent.get_location_from_path('/c4x/edX/toy/asset/sample_static.txt')
            content = contentstore().find(asset_location)
            self.assertEqual(content.locked, locked)

        def post_asset_update(lock):
            """ Helper method for posting asset update. """
            upload_date = datetime(2013, 6, 1, 10, 30, tzinfo=UTC)
            asset_location = Location(['c4x', 'edX', 'toy', 'asset', 'sample_static.txt'])
            location = loc_mapper().translate_location(course.location.course_id, course.location, False, True)
            url = location.url_reverse('assets/', '')

            resp = self.client.post(
                url,
                json.dumps(assets._get_asset_json("sample_static.txt", upload_date, asset_location, None, lock)),
                "application/json"
            )
            self.assertEqual(resp.status_code, 201)
            return json.loads(resp.content)

        # Load the toy course.
        module_store = modulestore('direct')
        _, course_items = import_from_xml(
            module_store,
            'common/test/data/',
            ['toy'],
            static_content_store=contentstore(),
            verbose=True
        )
        course = course_items[0]
        verify_asset_locked_state(False)

        # Lock the asset
        resp_asset = post_asset_update(True)
        self.assertTrue(resp_asset['locked'])
        verify_asset_locked_state(True)

        # Unlock the asset
        resp_asset = post_asset_update(False)
        self.assertFalse(resp_asset['locked'])
        verify_asset_locked_state(False)


class TestAssetIndex(CourseTestCase):
    """
    Test getting asset lists via http (Note, the assets don't actually exist)
    """
    def setUp(self):
        """
        Create fake asset entries for the other tests to use
        """
        super(TestAssetIndex, self).setUp()
        self.entry_filter = self.create_asset_entries(contentstore(), 100)
        location = loc_mapper().translate_location(self.course.location.course_id, self.course.location, False, True)
        self.url = location.url_reverse('assets/', '')

    def tearDown(self):
        """
        Get rid of the entries
        """
        contentstore().fs_files.remove(self.entry_filter)

    def create_asset_entries(self, cstore, number):
        """
        Create the fake entries
        """
        course_filter = Location(
            XASSET_LOCATION_TAG, category='asset', course=self.course.location.course, org=self.course.location.org
        )
        # purge existing entries (a bit brutal but hopefully tests are independent enuf to not trip on this)
        cstore.fs_files.remove(location_to_query(course_filter))
        base_entry = {
            'displayname': 'foo.jpg',
            'chunkSize': 262144,
            'length': 0,
            'uploadDate': datetime(2012, 1, 2, 0, 0),
            'contentType': 'image/jpeg',
        }
        for i in range(number):
            base_entry['displayname'] = '{:03x}.jpeg'.format(i)
            base_entry['uploadDate'] += timedelta(hours=i)
            base_entry['_id'] = course_filter.replace(name=base_entry['displayname']).dict()
            cstore.fs_files.insert(base_entry)

        return course_filter.dict()

    ASSET_LIST_RE = re.compile(r'AssetCollection\((.*)\);$', re.MULTILINE)
