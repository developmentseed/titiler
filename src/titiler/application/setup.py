"""Setup titiler.application."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "titiler.core==0.11.0",
    "titiler.extensions[cogeo,stac]==0.11.0",
    "titiler.mosaic==0.11.0",
    "starlette-cramjam>=0.3,<0.4",
    "python-dotenv",
]
extra_reqs = {
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "httpx", "brotlipy"],
    "server": ["uvicorn[standard]>=0.12.0,<0.19.0"],
}


setup(
    name="titiler.application",
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
    keywords="COG STAC MosaicJSON FastAPI",
    author="Vincent Sarago",
    author_email="vincent@developmentseed.org",
    url="https://github.com/developmentseed/titiler",
    license="MIT",
    packages=find_namespace_packages(exclude=["tests*"]),
    package_data={"titiler": ["application/templates/*.html"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
