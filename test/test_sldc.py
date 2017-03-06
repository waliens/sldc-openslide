from unittest import TestCase
import os
import numpy as np
from PIL.Image import fromarray
from PIL.ImageDraw import ImageDraw
from shapely.geometry import Point
from sldc import PolygonClassifier
from sldc import Segmenter
from sldc import WorkflowBuilder

from sldc_openslide import OpenSlideImage


class CircleSegmenter(Segmenter):
    def segment(self, image):
        """Segment a grey circle in black image"""
        segmented = (image[:, :, 0] > 50)
        return segmented.astype("uint8") * 255


class CircleClassifier(PolygonClassifier):
    def predict(self, image, polygon):
        """A polygon classifier which always predict 1 with a probablility 1.0"""
        return 1, 1.0


def relative_error(val, ref):
    return np.abs(val - ref) / ref


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
        self.filename = os.path.join(os.path.dirname(__file__), "sldc_test_image.tif")

    def testDetectCircle(self):
        """A test which executes a full workflow on image containing a white circle in the center of an black image
        """
        # build workflow
        builder = WorkflowBuilder()
        builder.set_segmenter(CircleSegmenter())
        builder.add_catchall_classifier(CircleClassifier())
        workflow = builder.get()

        # process image
        image = OpenSlideImage(self.filename)
        workflow_info = workflow.process(image)

        # Check results
        self.assertEqual(len(workflow_info.polygons), 1)

        # Check circle
        polygon = workflow_info.polygons[0]
        self.assertEqual(relative_error(polygon.area, np.pi * 750 * 750) <= 0.005, True)
        self.assertEqual(relative_error(polygon.centroid.x, 1000) <= 0.005, True)
        self.assertEqual(relative_error(polygon.centroid.y, 1000) <= 0.005, True)
        self.assertEqual(workflow_info.classes, [1])
        self.assertEqual(workflow_info.probas, [1.0])
        self.assertEqual(workflow_info.dispatch, ["catchall"])

    def testDetectCircleParallel(self):
        """A test which executes a full workflow on image containing a white circle in the center of an black image in
        parallel
        """
        # generate circle image
        w, h = 2000, 2000
        image = np.zeros((w, h, 3), dtype="uint8")
        image = draw_circle(image, 750, (1000, 1000), color=[129, 129, 129])

        # build workflow
        builder = WorkflowBuilder()
        builder.set_n_jobs(2)
        builder.set_segmenter(CircleSegmenter())
        builder.add_catchall_classifier(CircleClassifier())
        builder.set_parallel_dc(True)
        workflow = builder.get()

        # process image
        image = OpenSlideImage(self.filename)
        workflow_info = workflow.process(image)

        # Check results
        self.assertEqual(len(workflow_info.polygons), 1)

        # Check circle
        polygon = workflow_info.polygons[0]
        self.assertEqual(relative_error(polygon.area, np.pi * 750 * 750) <= 0.005, True)
        self.assertEqual(relative_error(polygon.centroid.x, 1000) <= 0.005, True)
        self.assertEqual(relative_error(polygon.centroid.y, 1000) <= 0.005, True)
        self.assertEqual(workflow_info.classes, [1])
        self.assertEqual(workflow_info.probas, [1.0])
        self.assertEqual(workflow_info.dispatch, ["catchall"])
