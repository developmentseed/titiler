"""Setup titiler."""

from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "email-validator",
    "fastapi==0.60.1",
    "jinja2",
    "python-binary-memcached",
    "rio-color",
    "rio-tiler-crs==3.0b2",
]
extra_reqs = {
    "dev": ["pytest", "pytest-cov", "pytest-asyncio", "pre-commit", "requests"],
    "mosaic": ["cogeo-mosaic~=3.0a5"],
    "server": ["uvicorn", "click==7.0"],
    "lambda": ["mangum>=0.9.0"],
    "deploy": [
        "docker",
        "aws-cdk.core",
        "aws-cdk.aws_lambda",
        "aws-cdk.aws_apigatewayv2",
        "aws-cdk.aws_ecs",
        "aws-cdk.aws_ec2",
        "aws-cdk.aws_autoscaling",
        "aws-cdk.aws_ecs_patterns",
    ],
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "requests"],
}


setup(
    name="titiler",
    version="3.0.0",
    description=u"",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="COG STAC MosaicJSON FastAPI Serverless",
    author=u"Vincent Sarago",
    author_email="vincent@developmentseed.org",
    url="https://github.com/developmentseed/titiler",
    license="MIT",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    package_data={"titiler": ["templates/*.html", "templates/*.xml"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
