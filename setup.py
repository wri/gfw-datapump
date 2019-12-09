from setuptools import setup, find_packages

setup(
    name="geotrellis_summary_update",
    version="0.1.0",
    description="Common utils to run GeoTrellis job on EMR and update in Resource Watch datasets API.",
    packages=find_packages(),
    author="Justin Terry",
    license="MIT",
    # only list requirements for geotrellis_summary_update here
    # place requirements of lambda functions into requirement-dev.txt
    install_requires=["boto3~=1.10.7", "requests~=2.22.0",],  # noqa: E231
)
