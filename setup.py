import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()

with open(os.path.join(here, 'requirements.txt')) as f:
    requires = filter(None, f.readlines())

with open(os.path.join(here, 'VERSION')) as f:
    version = f.read().strip()

setup(name='unicore.hub',
      version=version,
      description='User authentication and data storage for Universal Core',
      long_description=README,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='Praekelt Foundation',
      author_email='dev@praekelt.com',
      url='http://github.com/universalcore/unicore.hub',
      license='BSD',
      keywords='authentication, universal, core',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      namespace_packages=['unicore'],
      install_requires=requires,
      tests_require=requires,
      entry_points="""\
      [paste.app_factory]
      main = unicore.hub.service:main
      [console_scripts]
      hubservice=unicore.hub.service.commands:in_app_env
      """,
      message_extractors={'.': [
          ('**.py', 'python', None),
          ('**.jinja2', 'jinja2', None),
      ]})
