import prend
from prend.constants import Constants
from setuptools import setup

setup(name='prend',
      version=prend.Constants.app_version,
      description=prend.Constants.app_desc,
      long_description=open('README.md').read(),
      keywords='openhab rule engine daemon rest',
      url='https://github.com/rosenloecher-it/prend',
      author='Raul Rosenlöcher',
      license='GPLv3',
      packages=['prend'],
      install_requires=[
          'aiohttp',
          'aiosseclient',
          'multiprocessing-logging',
          'py-dateutil',
          'requests',
          'schedule'
      ],
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)
