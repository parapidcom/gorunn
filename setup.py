from setuptools import setup, find_packages
from gorunn import __version__


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='gorunn',
    version=__version__,
    author='Goran Parapid',
    author_email='goran@parapid.com',
    description='CLI tool for managing local environments',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/parapidcom/gorunn',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': [
            'gorunn/templates/*/*',
            'gorunn/templates/**/**/*'
        ]
    },
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'gorunn=gorunn.cli:cli'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS',
    ],
    python_requires='>=3.9',
)
