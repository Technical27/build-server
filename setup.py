from setuptools import setup

setup(
    name='build-server',
    version='0.0.0',
    install_requires=['PyGithub','pygit2','python-dotenv'],
    include_package_data=True,
    zip_safe=True,
    scripts=['bin/build-server']
)
