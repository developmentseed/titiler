"""Setup titiler.core."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "fastapi>=0.87.0",
    "geojson-pydantic",
    "jinja2>=2.11.2,<4.0.0",
    "numpy",
    "pydantic",
    "rasterio",
    "rio-tiler>=4.1,<4.2",
    "simplejson",
    "importlib_resources>=1.1.0;python_version<'3.9'",
    "typing_extensions;python_version<'3.8'",
]
extra_reqs = {
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "httpx"],
}


setup(
    name="titiler.core",
    description="A modern dynamic tile server built on top of FastAPI and Rasterio/GDAL.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="COG STAC FastAPI",
    author="Vincent Sarago",
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
