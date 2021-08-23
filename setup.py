"""Setup titiler metapackage."""

from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

__version__ = "0.3.6"

inst_reqs = [
    f"titiler.core=={__version__}",
    f"titiler.mosaic=={__version__}",
    f"titiler.application=={__version__}",
]


setup(
    name="titiler",
    version=__version__,
    description="A modern dynamic tile server built on top of FastAPI and Rasterio/GDAL.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.6",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords="COG STAC MosaicJSON FastAPI Tile Server Dynamic",
    author="Vincent Sarago",
    author_email="vincent@developmentseed.org",
    url="https://github.com/developmentseed/titiler",
    license="MIT",
    zip_safe=False,
    install_requires=inst_reqs,
    packages=[],
)
