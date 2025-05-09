# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Plugin Server'
copyright = '2025, Nicole Stevens'
author = 'Nicole Stevens'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['myst_parser']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'sphinx_rtd_theme'
html_theme = "sphinx_material"
html_static_path = ['_static']

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}
master_doc = 'index'


# Material theme options (minimal dark mode)
html_theme_options = {
    # Set the name of the project to appear in the sidebar
    'nav_title': 'Plugin Server',

    # Set the color and the accent color
    'color_primary': 'grey',
    'color_accent': 'deep-orange',

    # Set the repo location to get a badge with stats
    'repo_url': 'https://github.com/nicciniamh/pluginserver',
    'repo_name': 'Plugin Server',

    # Configure the palette to use dark mode
    'theme_color': 'black',  # for meta theme-color
    'globaltoc_depth': 2,
    'globaltoc_collapse': True,
    'globaltoc_includehidden': True,

    'master_doc': False,  # suppress 'Contents' heading

    # Dark mode palette config
    'palette': [
        {
            'media': '(prefers-color-scheme: dark)',
            'scheme': 'slate',
            'primary': 'grey',
            'accent': 'deep-orange',
            'toggle': {
                'icon': 'material/weather-sunny',
                'name': 'Switch to light mode',
            },
        },
        {
            'media': '(prefers-color-scheme: light)',
            'scheme': 'default',
            'primary': 'grey',
            'accent': 'deep-orange',
            'toggle': {
                'icon': 'material/weather-night',
                'name': 'Switch to dark mode',
            },
        },
    ],
}

