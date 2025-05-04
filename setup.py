from setuptools import setup

## setuptool config for pluginserver

setup(
    name='pluginserver',
    version='0.6.2',
    packages=['plugincore'],
    include_package_data=True,
    description='Plugin-driven API server',
    long_description='A REST-like API Server built on asyncio and aiohttp, leverageing plugins for actual api management',
    author='Nicole Stevens',
    url='https://github.com/nicciniamh/pluginserver',
    license='Apache2.0',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'aiohttp',
	'aiohttp_cors',
    ],
    entry_points={
        'console_scripts': [
            'pserve = plugincore.pserv:main',
        ],
    },
    project_urls={
        'Documentation': 'https://pluginserver.readthedocs.io', 
    }
)
