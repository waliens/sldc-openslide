from unittest import TestCase
import os

import sldc
from PIL import Image
import numpy as np
from numpy.testing import assert_array_equal
from openslide import OpenSlide, open_slide

from sldc_openslide import OpenSlideImage
from sldc_openslide import OpenSlideTileBuilder


class FakeImage(sldc.Image):
    @property
    def channels(self):
        return 3

    @property
    def np_image(self):
        return np.array([[[1, 2, 1]]])

    @property
    def width(self):
        return 1

    @property
    def height(self):
        return 1


class TestOpenSlideImage(TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(__file__), "test.tif")
        self.png_filename = os.path.join(os.path.dirname(__file__), "test.png")
        self.width, self.height = 1169, 1027
        self.level_count = 4

    def testOpenSlideImage(self):
        image = OpenSlideImage(self.filename)
        self.assertEqual(image.width, self.width)
        self.assertEqual(image.height, self.height)
        self.assertEqual(image.level_count, self.level_count)
        self.assertEqual(image.zoom_level, 0)  # default level should be zero
        self.assertEqual(image.channels, 3)  # always 3 channels
        self.assertFalse(image.has_resolution)  # by default no resolution
        self.assertIsNone(image.resolution)  # default resolution is None
        self.assertIsNotNone(image.slide)
        # full image loading
        with self.assertRaises(NotImplementedError):
            _ = image.np_image
        # test setters
        new_resolution = 25
        image.resolution = new_resolution
        self.assertEqual(image.resolution, new_resolution)
        new_zoom_level = 3
        image.zoom_level = new_zoom_level
        self.assertEqual(image.zoom_level, new_zoom_level)
        invalid_new_zoom_level = self.level_count + 1
        with self.assertRaises(ValueError):
            image.zoom_level = invalid_new_zoom_level
        image.close()

    def testOpenSlideTileBuilder(self):
        image = OpenSlideImage(self.filename)
        tile_builder = OpenSlideTileBuilder()

        # get tile box
        offset = (0, 0)
        width, height = 125, 100
        tile = tile_builder.build(image, offset, width, height)
        slide = OpenSlide(self.filename)
        os_image = slide.read_region(offset, 0, (width, height))
        tile_image = tile.np_image
        assert_array_equal(tile_image, os_image)

        # test with invalid base image
        fake_image = FakeImage()
        invalid_tile = tile_builder.build(fake_image, offset, width, height)
        with self.assertRaises(ValueError):
            _ = invalid_tile.np_image
        image.close()

    def testOpenSlideImageWithZoom(self):
        zoom_level = 1
        os_image = open_slide(self.filename)
        image = OpenSlideImage(self.filename, zoom_level=zoom_level)

        # test dimensions
        self.assertEqual(os_image.level_dimensions[zoom_level], (image.width, image.height))

        # test topology
        tile_width = tile_height = 300
        topology = image.tile_topology(OpenSlideTileBuilder(), max_height=tile_height, max_width=tile_width, overlap=0)
        self.assertEqual(topology.tile_count, 4)
        tile = topology.tile(1)
        self.assertEqual(tile.offset, (0, 0))
        self.assertEqual(tile.width, tile_width)
        self.assertEqual(tile.height, tile_height)
        tile2 = topology.tile(4)
        self.assertEqual(tile2.offset, (tile_width, tile_height))
        self.assertEqual(tile2.width, image.width - tile_width)
        self.assertEqual(tile2.height, image.height - tile_height)
