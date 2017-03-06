from unittest import TestCase
import os
import numpy as np
from PIL.Image import fromarray
from PIL.ImageDraw import ImageDraw
from shapely.geometry import Point
from sldc import DispatchingRule
from sldc import PolygonClassifier
from sldc import Segmenter
from sldc import WorkflowBuilder

from sldc_openslide import OpenSlideImage
from sldc_openslide import OpenSlideTileBuilder


class TifImageSegmenter(Segmenter):
    def segment(self, image):
        """Segment a grey circle in black image"""
        segmented = (image[:, :, 0] < 200)
        return segmented.astype(np.uint8) * 255


class CircleSegmenter(Segmenter):
    def segment(self, image):
        """Segment a grey circle in black image"""
        segmented = (image[:, :, 0] > 50)
        return segmented.astype(np.uint8) * 255


class DumbClassifier(PolygonClassifier):
    def predict(self, image, polygon):
        """A polygon classifier which always predict 1 with a probablility 1.0"""
        return 1, 1.0


class CircleRule(DispatchingRule):
    def evaluate(self, image, polygon):
        """Return true if the polyon is a circle"""
        return circularity(polygon) > 0.85


def relative_error(val, ref):
    return np.abs(val - ref) / ref


def circularity(polygon):
    return 4 * np.pi * polygon.area / (polygon.length * polygon.length)


def draw_poly(image, polygon, color=255):
    """Draw a polygon in the given color at the given location"""
    pil_image = fromarray(image)
    validated_color = color
    draw = ImageDraw(pil_image)
    if len(image.shape) > 2 and image.shape[2] > 1:
        validated_color = tuple(color)
    draw.polygon(polygon.boundary.coords, fill=validated_color, outline=validated_color)
    return np.asarray(pil_image)


def draw_circle(image, radius, center, color=255, return_circle=False):
    """Draw a circle of radius 'radius' and centered in 'centered'

    Parameters
    ----------
    color: iterable
    """
    circle_center = Point(*center)
    circle_polygon = circle_center.buffer(radius)
    image_out = draw_poly(image, circle_polygon, color)
    if return_circle:
        return image_out, circle_polygon
    else:
        return image_out


class TestWithinOpenSlideImageWithinSLDC(TestCase):
    def setUp(self):
        self.filename_png = os.path.join(os.path.dirname(__file__), "sldc_test_image.png")
        self.filename_tif = os.path.join(os.path.dirname(__file__), "test.tif")

    def testDetectCircle(self):
        """A test which executes a full workflow on image containing a white circle in the center of an black image
        """
        # build workflow
        builder = WorkflowBuilder()
        builder.set_tile_builder(OpenSlideTileBuilder())
        builder.set_segmenter(CircleSegmenter())
        builder.add_classifier(CircleRule(), DumbClassifier(), dispatching_label="circle")
        workflow = builder.get()

        # process image
        image = OpenSlideImage(self.filename_png)
        workflow_info = workflow.process(image)

        # Check results
        self.assertEqual(len(workflow_info.polygons),  5)
        self.assertEqual(len([d for d in workflow_info.dispatch if d is not None]), 2)

    def testDetectCircleParallelWithPng(self):
        """A test which executes a full workflow on image containing a white circle in the center of an black image in
        parallel
        """
        # build workflow
        builder = WorkflowBuilder()
        builder.set_n_jobs(2)
        builder.set_parallel_dc(True)
        builder.set_tile_builder(OpenSlideTileBuilder())
        builder.set_segmenter(CircleSegmenter())
        builder.add_classifier(CircleRule(), DumbClassifier(), dispatching_label="circle")
        workflow = builder.get()

        # process image
        image = OpenSlideImage(self.filename_png)
        workflow_info = workflow.process(image)

        # Check results
        self.assertEqual(len(workflow_info.polygons),  5)
        self.assertEqual(len([d for d in workflow_info.dispatch if d is not None]), 2)

    def testDetectCircleParallelWithTif(self):
        """A test which executes a full workflow on image containing a white circle in the center of an black image in
        parallel. With a tif, openslide uses a ctype object which might cause trouble at pickling (-> need for testing).
        """
        # build workflow
        builder = WorkflowBuilder()
        builder.set_n_jobs(2)
        builder.set_parallel_dc(True)
        builder.set_tile_builder(OpenSlideTileBuilder())
        builder.set_segmenter(TifImageSegmenter())
        builder.add_catchall_classifier(DumbClassifier())
        workflow = builder.get()

        # process image
        image = OpenSlideImage(self.filename_tif)
        workflow_info = workflow.process(image)

        # Check results
        self.assertEqual(len(workflow_info.polygons), 25)
