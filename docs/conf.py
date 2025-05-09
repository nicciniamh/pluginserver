# -- Project information -----------------------------------------------------
project = 'Plugin Server'
copyright = '2025, Nicole Stevens'
author = 'Nicole Stevens'

# -- General configuration ---------------------------------------------------
extensions = [
    'myst_parser',  # Markdown support
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'furo'  # Furo theme for ReadTheDocs
html_static_path = ['_static']

# Set the Pygments style for code highlighting
#pygments_style = 'github-dark'  # GitHub dark theme for Pygments

html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#06249a",
        "color-brand-content": "#062d9a",
    },
    "dark_css_variables": {
        "color-brand-primary": "#3445e2",
        "color-brand-content": "#3734e2",
    },
}

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',  # Markdown files with myst-parser
}
master_doc = 'index'

# -- Additional configurations ----------------------------------------------
# If you have any other settings like `autodoc` or `intersphinx`, include them here.

html_css_files = [
    'custom.css',  # Include the custom CSS file
]

