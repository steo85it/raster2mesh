# distutils: define_macros=NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION

from setuptools import Extension, setup

DISTNAME = 'raster2mesh'

setup(
    name=DISTNAME,
    packages=['raster2mesh']
)
