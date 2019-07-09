from distutils.core import setup

from certification_service._version import __version__

setup(
    name='certification-service',
    version=__version__,
    description='Web service to run ESGF certification runs',
    author='Jason',
    author_email='boutte3@llnl.gov',
    url='https://github.com/esgf-compute/certification-service',
    packages=['certification_service'],
)
