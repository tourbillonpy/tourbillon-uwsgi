import sys
from setuptools import setup, find_packages


PY34_PLUS = sys.version_info[0] == 3 and sys.version_info[1] >= 4

exclude = ['tourbillon.uwsgi.uwsgi2'
           if PY34_PLUS else 'tourbillon.uwsgi.uwsgi']

install_requires = []

if not PY34_PLUS:
    install_requires.append('trollius==2.0')


setup(
    name='tourbillon-uwsgi',
    version='0.1',
    packages=find_packages(exclude=exclude),
    zip_safe=False,
    namespace_packages=['tourbillon'],
    install_requires=install_requires
)
