import os
import tempfile
from unittest import mock

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase, override_settings

from oscar.apps.catalogue.abstract_models import MissingServiceImage
from oscar.test import factories
from oscar.test.utils import EASY_THUMBNAIL_BASEDIR, ThumbnailMixin


class TestServiceImages(ThumbnailMixin, TestCase):

    def _test_service_images_and_thumbnails_deleted_when_service_deleted(self):
        service = factories.create_service()
        images_qty = 3
        self.create_service_images(qty=images_qty, service=service)

        assert service.images.count() == images_qty
        thumbnails_full_paths = self.create_thumbnails()

        service.delete()

        self._test_images_folder_is_empty()
        self._test_thumbnails_not_exist(thumbnails_full_paths)

    @override_settings(
        OSCAR_THUMBNAILER='oscar.core.thumbnails.SorlThumbnail',
    )
    def test_thumbnails_deleted_sorl_thumbnail(self):
        self._test_service_images_and_thumbnails_deleted_when_service_deleted()

    @override_settings(
        THUMBNAIL_BASEDIR=EASY_THUMBNAIL_BASEDIR,
        OSCAR_THUMBNAILER='oscar.core.thumbnails.EasyThumbnails',
    )
    def test_thumbnails_deleted_easy_thumbnails(self):
        self._test_service_images_and_thumbnails_deleted_when_service_deleted()

    def test_images_are_in_consecutive_order(self):
        service = factories.create_service()
        for i in range(4):
            factories.create_service_image(service=service, display_order=i)

        service.images.all()[2].delete()

        for idx, im in enumerate(service.images.all()):
            self.assertEqual(im.display_order, idx)

    def test_variant_images(self):
        parent = factories.ServiceFactory(structure='parent')
        variant = factories.create_service(parent=parent)
        factories.create_service_image(service=variant, caption='Variant Image')
        all_images = variant.get_all_images()
        self.assertEqual(all_images.count(), 1)
        service_image = all_images.first()
        self.assertEqual(service_image.caption, 'Variant Image')

    def test_variant_images_fallback_to_parent(self):
        parent = factories.ServiceFactory(structure='parent')
        variant = factories.create_service(parent=parent)
        factories.create_service_image(service=parent, caption='Parent Service Image')
        all_images = variant.get_all_images()
        self.assertEqual(all_images.count(), 1)
        service_image = all_images.first()
        self.assertEqual(service_image.caption, 'Parent Service Image')


class TestMissingServiceImage(StaticLiveServerTestCase):

    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @mock.patch('oscar.apps.catalogue.abstract_models.find')
    def test_symlink_creates_directories(self, mock_find):
        # Create a fake empty file to symlink
        img = tempfile.NamedTemporaryFile(delete=False)
        img.close()

        mock_find.return_value = img.name
        # Initialise the class with a nested path
        path = 'image/path.jpg'
        MissingServiceImage(path)
        # Check that the directory exists
        image_path = os.path.join(self.TEMP_MEDIA_ROOT, path)
        self.assertTrue(os.path.exists(image_path))

        # Clean up
        for f in [image_path, img.name]:
            os.unlink(f)
        for d in [os.path.join(self.TEMP_MEDIA_ROOT, 'image'), self.TEMP_MEDIA_ROOT]:
            os.rmdir(d)

    @override_settings(MEDIA_ROOT='')
    @mock.patch('oscar.apps.catalogue.abstract_models.MissingServiceImage.symlink_missing_image')
    def test_no_symlink_when_no_media_root(self, mock_symlink):
        MissingServiceImage()
        self.assertEqual(mock_symlink.call_count, 0)
