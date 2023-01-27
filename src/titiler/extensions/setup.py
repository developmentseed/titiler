"""Setup titiler.extensions."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = ["titiler.core==0.11.0"]
extra_reqs = {
    "cogeo": ["rio-cogeo>=3.1,<4.0"],
    "stac": ["rio-stac>=0.6,<0.7"],
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "httpx", "jsonschema>=3.0"],
}


setup(
    name="titiler.extensions",
    description="Extensions for TiTiler Factories",
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
    keywords="TiTiler",
    author="Vincent Sarago",
    author_email="vincent@developmentseed.org",
    url="https://github.com/developmentseed/titiler",
    license="MIT",
    packages=find_namespace_packages(exclude=["tests*"]),
    package_data={
        "titiler": ["extensions/templates/*.html", "extensions/templates/*.xml"]
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
