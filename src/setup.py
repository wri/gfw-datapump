from setuptools import find_packages, setup

setup(
    name="datapump",
    version="0.2.0",
    description="Data pipelines to ingest, analyze, and store new data.",
    packages=find_packages(),
    author="Justin Terry",
    license="MIT",
    install_requires=[
        "boto3~=1.10.7",
        "requests~=2.22.0",
        "geojson~=2.5.0",
        "google-cloud-storage~=2.1.0",
        "pyshp~=2.1.0",
        "pydantic~=1.7.2",
        "smart-open~=4.0.1",
        "retry~=0.9.2",
    ],  # noqa: E231
)
