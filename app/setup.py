import sys
from setuptools import setup, find_packages, find_namespace_packages

NAME = "hitepapp"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = []

print(find_namespace_packages(include=['hitep.*', 'hitep_service.*'], where='src')
              + find_namespace_packages(include=['hitep.*', 'hitep_service.*'], where='src_gen'))

setup(
    name=NAME,
    version=VERSION,
    description="TEP REST API",
    author_email="p.t.j.m.vossen@vu.nl",
    url="",
    keywords=["OpenAPI", "TEP REST API"],
    install_requires=REQUIRES,
    package_dir={'': 'src'},
    packages=find_namespace_packages(include=['hitep.*', 'hitep_service.*'], where='src'),
    package_data={'': ['py-app/leolani-tep-api.yaml'], 'hitep_service.importance': ['queries/*', 'queries/**/*']},
    include_package_data=True,
    long_description="""\
    REST API specification for integration of TEP components  Some useful links: - [The repository](https://github.com/hi-tep/tep-rest-api) - [Leolani](https://github.com/leolani) - [EMISSOR](https://github.com/leolani/emissor)
    """
)

