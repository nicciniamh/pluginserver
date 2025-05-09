# -- Project information -----------------------------------------------------
project = 'Plugin Server'
copyright = '2025, Nicole Stevens'
author = 'Nicole Stevens'

# -- General configuration ---------------------------------------------------
extensions = [
    'myst_parser',  # Markdown support
    'sphinx_github_style',  # GitHub style theme
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'furo'  # Furo theme for ReadTheDocs
html_static_path = ['_static']

# Set the Pygments style for code highlighting
pygments_style = 'github-dark'  # GitHub dark theme for Pygments

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

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',  # Markdown files with myst-parser
}
master_doc = 'index'

# -- Additional configurations ----------------------------------------------
# If you have any other settings like `autodoc` or `intersphinx`, include them here.

