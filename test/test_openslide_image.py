from unittest import TestCase
import os
from PIL import Image
import numpy as np

from sldc_openslide import OpenSlideImage


class TestOpenSlideImage(TestCase):
    def setUp(self):
        self.filename = "test.tif"
        self.width, self.height = 1200, 1400
        fake_image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        Image.fromarray(fake_image).save()

    def tearDown(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)

    def testOpenSlideImage(self):
        image = OpenSlideImage(self.filename)
        self.assertEqual(image.width, self.width)
        self.assertEqual(image.height, self.height)
