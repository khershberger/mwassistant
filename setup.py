try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

setup(name = 'pysmith',
      description = 'Tools for visualizing and manipulating S-Parameters',
      authon = 'Kyle Hershberger',
      version = '0.1.0',
      packages = find_packages(),
      install_requires = [
          'matplotlib',
          'numpy',
          'pyqt',
          'qtconsole',
          'scikit-rf'
          ]
      )
