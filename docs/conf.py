# -- Project information -----------------------------------------------------
project = 'Plugin Server'
copyright = '2025, Nicole Stevens'
author = 'Nicole Stevens'

# -- General configuration ---------------------------------------------------
extensions = [
    'myst_parser',     # Markdown support
#    'sphinx_github_style', # Enable the github-style theme/extension
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'furo' # You can try changing this to a theme provided by sphinx-github-style if it has one
html_title = "Plugin Server"
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',    # Markdown files with myst-parser
}
master_doc = 'index'

# -- Configuration for sphinx-github-style ------------------------------------
#linkcode_url = "https://github.com/nicciniamh/pluginserver"
