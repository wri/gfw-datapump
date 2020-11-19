from setuptools import setup, find_packages

setup(
    name="datapump",
    version="0.2.0",
    description="Common utils to run GeoTrellis job on EMR and update in data API.",
    packages=find_packages(),
    author="Justin Terry",
    license="MIT",
    install_requires=[
        "boto3~=1.10.7",
        "requests~=2.22.0",
        "geojson~=2.5.0",
        "pyshp~=2.1.0",
        "pydantic~=1.7.2",
    ],  # noqa: E231
)
