import numpy as np
from sldc import Image, Tile, TileBuilder
from openslide import OpenSlide


class OpenSlideImage(Image):
    """Object representing an OpenSlide image from a given file"""
    def __init__(self, filename, resolution=None, zoom_level=0):
        """ Construct an openslide image
        Parameters
        ----------
        filename: str
            The path to the whole-slide image file
        resolution: int/float
            The resolution of the image (e.g. in micrometer squared per pixel squared
        zoom_level: int
            Zoom level at which the image must be read. 0 for finest resolution, > 0 for coarser resolutions.
        """
        self._filename = filename
        self._slide = OpenSlide(filename=filename)
        self._resolution = resolution
        self._level = self._validate_zoom_level(zoom_level)

    @property
    def height(self):
        return self._slide.dimensions[1]

    @property
    def np_image(self):
        raise NotImplementedError("Not implemented because of potential OOM due to image size."
                                  "Use OpenSlideTile with a TileTopology to explore the image.")

    @property
    def width(self):
        return self._slide.dimensions[0]

    @property
    def channels(self):
        return 3  # todo checks whether this can change ?

    @property
    def resolution(self):
        return self._resolution

    @resolution.setter
    def resolution(self, res):
        self._resolution = res

    @property
    def has_resolution(self):
        return self._resolution is not None

    @property
    def zoom_level(self):
        return self._level

    @zoom_level.setter
    def zoom_level(self, zoom_level):
        self._level = self._validate_zoom_level(zoom_level)

    @property
    def level_count(self):
        return self._slide.level_count

    def _validate_zoom_level(self, zoom_level):
        """Checks whether the given zoom level is valid for the current image"""
        if not (0 <= zoom_level < self._slide.level_count):
            raise ValueError("Invalid zoom level {} for image '{}'. Must be in range [0, {}[".format(
                self._level, self._filename,
                self._slide.level_count
            ))
        return zoom_level

    @property
    def slide(self):
        """Return the OpenSlide object representing the slide"""
        return self._slide


class OpenSlideTile(Tile):
    """Represent a tile from an openslide image"""
    @property
    def np_image(self):
        base_image = self.base_image
        if not isinstance(base_image, OpenSlideImage):
            raise ValueError("Base image should be an OpenSlideImage object, found '{}'.".format(type(base_image)))
        offset = self.abs_offset
        zoom_level = base_image.zoom_level
        size = (self.width, self.height)
        return np.asarray(base_image.slide.read_region(offset, zoom_level, size))


class OpenSlideTileBuilder(TileBuilder):
    """A builder for building OpenSlideTile objects"""
    def build(self, image, offset, width, height, polygon_mask=None):
        return OpenSlideTile(image, offset, width, height, polygon_mask=polygon_mask)
