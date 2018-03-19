from setuptools import setup, find_packages

long_description = "Utilities for working with Weka arff files"

setup(
    name='arffutils',
    version='0.1.0',
    description=long_description,
    long_description=long_description,
    license='GPLv3',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],

    keywords='weka arff utilities',

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    setup_requires=['nose>=1.0'],   # run tests with python setup.py nosetests

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'arffmerge=arffutils.arffmerge:main',
            'arffselect=arffutils.arffselect:main',
            'arffsplit=arffutils.arffsplit:main',
            'arffmetrics=arffutils.arffmetrics:main',
        ],
    },
    url='https://github.com/moygit/arffutils',
    author='Moy Easwaran',
)
