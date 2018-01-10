try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name = 'pysmith',
      description = 'Tools for visualizing and manipulating S-Parameters',
      authon = 'Kyle Hershberger',
      version = '0.1.0',
      packages = ['pysmith'],
      install_requires = [
          'pyqt5',
          'scikit-rf',
          'matplotlib',
          'numpy'
          ]
      )
