import setuptools
import sys
import os

from serializepy.version import VERSION


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="serializepy",
    version=VERSION,
    author="Jeppe Rask",
    author_email="jepperaskdk@gmail.com",
    description="Serialize and deserialize using type hints",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jepperaskdk/serializepy",
    project_urls={
        "Bug Tracker": "https://github.com/jepperaskdk/serializepy/issues",
    },
    package_dir={"": "."},
    packages=setuptools.find_packages(),
    license_files=('LICENSE',),
    python_requires=">=3.6",
)
