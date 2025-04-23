from setuptools import setup

setup(
    name='pluginserver',  # still the project name; no need to rename this unless you want
    version='0.3',
    packages=['plugincore'],  # matches the new directory name
    include_package_data=True,
    install_requires=[
        'aiohttp',
	'aiohttp_cors',
    ],
    entry_points={
        'console_scripts': [
            'pserve = plugincore.pserv:main',  # updated module path
        ],
    },
)
