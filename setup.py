"""Setup titiler."""

from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "brotli-asgi>=1.0.0",
    "cogeo-mosaic>=3.0.0rc2,<3.1",
    "fastapi==0.63.0",
    "geojson-pydantic",
    "jinja2>=2.11.2,<3.0.0",
    "morecantile",
    "numpy",
    "pydantic",
    "python-dotenv",
    "rasterio",
    "rio-cogeo>=2.1,<2.2",
    "rio-tiler>=2.0.4,<2.1",
    "uvicorn[standard]>=0.12.0,<0.14.0",
    # Additional requirements for python 3.6
    "dataclasses;python_version<'3.7'",
    "async_exit_stack>=1.0.1,<2.0.0;python_version<'3.7'",
    "async_generator>=1.10,<2.0.0;python_version<'3.7'",
]
extra_reqs = {
    "dev": ["pytest", "pytest-cov", "pytest-asyncio", "pre-commit", "requests"],
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "requests"],
    "docs": ["nbconvert", "mkdocs", "mkdocs-material", "mkdocs-jupyter", "pygments"],
}


setup(
    name="titiler",
    version="0.1.0",
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
    ],
    keywords="COG STAC MosaicJSON FastAPI",
    author=u"Vincent Sarago",
    author_email="vincent@developmentseed.org",
    url="https://github.com/developmentseed/titiler",
    license="MIT",
    packages=find_packages(exclude=["tests*"]),
    package_data={"titiler": ["templates/*.html", "templates/*.xml"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
