import sys
from setuptools import setup, find_packages

NAME = "hitep.openapi_server"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "connexion>=2.0.2",
    "swagger-ui-bundle>=0.0.2",
    "python_dateutil>=2.6.0"
]

setup(
    name=NAME,
    version=VERSION,
    description="TEP REST API",
    author_email="p.t.j.m.vossen@vu.nl",
    url="",
    keywords=["OpenAPI", "TEP REST API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['openapi/openapi.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['hitep.openapi_server=hitep.openapi_server.__main__:main']},
    long_description="""\
    REST API specification for integration of TEP components  Some useful links: - [The repository](https://github.com/hi-tep/tep-rest-api) - [Leolani](https://github.com/leolani) - [EMISSOR](https://github.com/leolani/emissor)
    """
)

