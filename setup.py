"""Setup titiler."""

from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    # There is a breaking change in starlette 0.14 which is not compatible with fastapi 0.61
    # Fastapi requires 0.13.6 but brotli-asgi ask for >=0.13.4 which results in starlette 0.14 being installed
    # we put fastapi as the first requirement to make sure starlette version is define by fastapi.
    "fastapi~=0.61",
    "brotli-asgi>=1.0.0",
    "email-validator",
    "jinja2",
    "python-dotenv",
    "rio-cogeo~=2.0",
    "rio-tiler>=2.0.0rc2,<2.1",
    "cogeo-mosaic>=3.0.0a17,<3.1",
]
extra_reqs = {
    "dev": ["pytest", "pytest-cov", "pytest-asyncio", "pre-commit", "requests"],
    "server": ["uvicorn"],
    "lambda": ["mangum>=0.10.0"],
    "deploy": [
        "docker",
        "python-dotenv",
        "aws-cdk.core",
        "aws-cdk.aws_lambda",
        "aws-cdk.aws_apigatewayv2",
        "aws-cdk.aws_ecs",
        "aws-cdk.aws_ec2",
        "aws-cdk.aws_autoscaling",
        "aws-cdk.aws_ecs_patterns",
    ],
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "requests"],
    "docs": ["nbconvert", "mkdocs", "mkdocs-material", "mkdocs-jupyter", "pygments"],
}


setup(
    name="titiler",
    version="0.1.0a12",
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
        "Programming Language :: Python :: 3.8",
    ],
    keywords="COG STAC MosaicJSON FastAPI Serverless",
    author=u"Vincent Sarago",
    author_email="vincent@developmentseed.org",
    url="https://github.com/developmentseed/titiler",
    license="MIT",
    packages=find_packages(exclude=["tests*", "stack"]),
    package_data={"titiler": ["templates/*.html", "templates/*.xml"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
