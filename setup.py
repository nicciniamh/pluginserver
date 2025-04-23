from setuptools import setup

## setuptool config for pluginserver

setup(
    name='pluginserver',
    version='0.3',
    packages=['plugincore'],
    include_package_data=True,
    install_requires=[
        'aiohttp',
	'aiohttp_cors',
    ],
    entry_points={
        'console_scripts': [
            'pserve = plugincore.pserv:main',
        ],
    },
)
