from setuptools import setup

setup(
    name="geotrellis_summary_update",
    version="0.1.0",
    description="Common utils to run GeoTrellis job on EMR and update in Resource Watch datasets API.",
    packages=["geotrellis_summary_update"],
    author="Justin Terry",
    license="MIT",
    install_requires=["requests~=2.22.0", "boto3~=1.10.7"],
)
