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
html_static_path = ['_static']

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}
master_doc = 'index'
html_theme = "furo"

# Set default Pygments style
pygments_style = "github-dark"  # Set a default; we'll handle the dynamic switch with JS

html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#4e9a06",
        "color-brand-content": "#4e9a06",
    },
    "dark_css_variables": {
        "color-brand-primary": "#8ae234",
        "color-brand-content": "#8ae234",
    },
}
extensions = [
    'sphinx_github_style',
]

pygments_style = 'github-dark'
