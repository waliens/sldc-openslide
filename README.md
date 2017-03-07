# SLDC-OpenSlide

[*__SLDC__*](https://github.com/waliens/sldc) is a Python library that aims at accelerating development of large images analysis workflows.
*SLDC-OpenSlide* is a Python binding for using *SLDC* with the *OpenSlide* image library. In practice, it enables workflows to process large images stored locally on disk.

[![Build status](https://travis-ci.org/waliens/sldc-openslide.svg?branch=master)](https://travis-ci.org/waliens/sldc-openslide)
[![codecov](https://codecov.io/gh/waliens/sldc-openslide/branch/master/graph/badge.svg)](https://codecov.io/gh/waliens/sldc-openslide)

## Install

1. Install SLDC: [https://github.com/waliens/sldc](https://github.com/waliens/sldc#install)
2. Install OpenSlide and openslide-python: [https://github.com/openslide/openslide-python](https://github.com/openslide/openslide-python#installation)
3. Install SLDC-OpenSlide:
    1. Clone or download the repository
    2. Move to the root folder
    3. Install: `python setup.py install`
4. Test your install: `python -c "import sldc_openslide"`

## Usage

*SLDC-OpenSlide* provides mostly two classes:

* `OpenSlideTileBuilder`: a builder that builds tiles using an `OpenSlideImage` as parent image. This is the tile builder that must be passed to the builder at the workflow construction.
* `OpenSlideImage`: adapts `OpenSlide` class to match *SLDC* `Image` interface. This is the `Image` object that must be passed to the `process` method of your workflow.