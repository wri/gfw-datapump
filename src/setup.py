from setuptools import find_packages, setup

setup(
    name="datapump",
    version="0.2.0",
    description="Data pipelines to ingest, analyze, and store new data.",
    packages=find_packages(),
    author="Justin Terry",
    license="MIT",
    install_requires=[
        "boto3~=1.26",
        "geojson~=3.0",
        "google-cloud-storage~=2.7",
        "pydantic~=1.10",
        "pyshp~=2.3",
        "requests~=2.28",
        "retry~=0.9",
        "smart-open~=6.0",
    ],  # noqa: E231
)
