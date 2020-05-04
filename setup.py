"""Setup titiler."""

from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "fastapi",
    "jinja2",
    "python-binary-memcached",
    "rio-color",
    "rio-tiler~=2.0a3",
    "email-validator",
]

extra_reqs = {
    "dev": ["pytest", "pytest-cov", "pytest-asyncio", "pre-commit"],
    "server": ["click==7.0", "uvicorn"],
    "deploy": [
        "aws-cdk.aws_apigateway",
        "aws-cdk.aws_autoscaling",
        "aws-cdk.aws_ec2",
        "aws-cdk.aws_ecs",
        "aws-cdk.aws_ecs_patterns",
        "aws-cdk.aws-lambda"
        "aws-cdk.core",
        "docker"
    ],
    "test": ["mock", "pytest", "pytest-cov", "pytest-asyncio", "requests"],
}

setup(
    name="titiler",
    version="0.1.0",
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
    keywords="",
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
