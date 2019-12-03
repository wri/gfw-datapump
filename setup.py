from setuptools import setup

setup(
    name="geotrellis_summary_update",
    version="0.1.0",
    description="Common utils to run GeoTrellis job on EMR and update in Resource Watch datasets API.",
    packages=["geotrellis_summary_update", "lambdas"],
    author="Justin Terry",
    license="MIT",
    install_requires=["boto3~=1.10.7", "requests~=2.22.0", "shapely~=1.6.4.post2"],
)
