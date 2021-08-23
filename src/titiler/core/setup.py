"""Setup titiler-core."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "fastapi>=0.65,<0.66",
    "geojson-pydantic",
    "jinja2>=2.11.2,<3.0.0",
    "morecantile",
    "numpy",
    "pydantic",
    "rasterio",
    "rio-tiler>=2.1,<2.2",
    # Additional requirements for python 3.6
    "async_exit_stack>=1.0.1,<2.0.0;python_version<'3.7'",
    "async_generator>=1.10,<2.0.0;python_version<'3.7'",
    "dataclasses;python_version<'3.7'",
    "importlib_resources>=1.1.0;python_version<'3.9'",
]
extra_reqs = {
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "requests"],
}


setup(
    name="titiler.core",
    version="0.3.6",
    description=u"A modern dynamic tile server built on top of FastAPI and Rasterio/GDAL.",
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
    keywords="COG STAC FastAPI",
    author=u"Vincent Sarago",
    author_email="vincent@developmentseed.org",
    url="https://github.com/developmentseed/titiler",
    license="MIT",
    packages=find_namespace_packages(exclude=["tests*"]),
    package_data={"titiler": ["core/templates/*.xml"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
