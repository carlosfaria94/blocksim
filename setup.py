from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    README = readme_file.read()

setup(
    name='blocksim',
    version='0.1',
    packages=find_packages('.'),
    install_requires=[
        'simpy',
        'schema',
        'scipy',
        'pysha3'
    ],
    author='Carlos Faria',
    author_email='carlosfigueira@tecnico.ulisboa.pt',
    description='A discrete event Blockchain simulator',
    license='MIT',
    long_description=README,
    python_requires='>=3.3',
    keywords='blocksim blockchain simulation discrete-event ethereum',
    url='https://github.com/BlockbirdStudio/blocksim',
    project_urls={
        'Bug Tracker': 'https://github.com/BlockbirdStudio/blocksim/issues',
        'Source Code': 'https://github.com/BlockbirdStudio/blocksim/tree/master/blocksim',
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering',
    ],
    entry_points={
        'console_scripts': [
            'blocksim = blocksim.main:run_simulation'
        ]
    },
)
