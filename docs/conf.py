# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Battery Data Toolkit'
copyright = '2024'
author = 'ROVI Team'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['nbsphinx']

templates_path = ['_templates']
exclude_patterns = ['_build']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
html_theme_options = {
    "logo": {
        "text": "BattData",
        "image_light": "_static/logo.png",
        "image_dark": "_static/logo.png",
    }
}
html_logo = '_static/logo.png'


# -- Options for NBSphinx -----------------------------------------------------

nbsphinx_execute = 'never'

# -- API Documentation --------------------------------------------------------

extensions.extend([
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinxcontrib.autodoc_pydantic',
    'sphinx_design'
])

autodoc_pydantic_model_show_json = False
autodoc_pydantic_settings_show_json = False

autoclass_content = 'both'

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'pyarrow': ('https://arrow.apache.org/docs/', None),
    'h5py': ('https://docs.h5py.org/en/stable/', None),
    'tables': ('https://www.pytables.org/', None)
}
