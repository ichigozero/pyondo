from setuptools import find_packages
from setuptools import setup

setup(
    name='pyondo',
    description='Raspberry Pi temperature monitor',
    author='Gary Sentosa',
    author_email='gary.sentosa@gmail.com',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'pigpio==1.46',
    ],
    entry_points='''
        [console_scripts]
        pyondo=pyondo.__main__:main
    ''',
)
