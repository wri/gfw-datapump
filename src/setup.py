from setuptools import find_packages, setup

setup(
    name="datapump",
    version="0.2.1",
    description="Data pipelines to ingest, analyze, and store new data.",
    packages=find_packages(),
    author="Justin Terry",
    license="MIT",
    install_requires=[
        "boto3~=1.28.30",
        "requests~=2.31.0",
        "geojson~=3.0.1",
        "google-cloud-storage~=2.10.0",
        "pyshp~=2.3.1",
        "pydantic~=1.10.11",
        "retry~=0.9.2",
    ],  # noqa: E231
)
