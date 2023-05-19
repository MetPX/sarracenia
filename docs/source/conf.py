# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

# -- Project information -----------------------------------------------------

import os,re

project = 'Sarracenia'
copyright = '2022, Shared Services Canada, Government of Canada, GPLv2'
author = 'Data Interchange Team'

hoho = os.getcwd()
print( f'current working directory {hoho}' )

file_ = '../sarracenia/__init__.py'
filepath = os.path.join(os.path.abspath('..'), file_)

with open(filepath) as fh:
    contents = fh.read().strip()

    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              contents, re.M)
    if version_match:
        version = version_match.group(1)
    else:
        version = 'UNKNOWN'

# The full version, including alpha/beta/rc tags
release = version



# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['nbsphinx', 
              'sphinx.ext.autodoc', 
              'sphinx.ext.coverage',
              'sphinx.ext.doctest',
              'sphinx.ext.githubpages',
              'sphinx.ext.ifconfig',
              'sphinx.ext.intersphinx',
              'sphinx.ext.napoleon',
              'sphinx.ext.todo',
              'sphinx.ext.viewcode']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#html_theme = 'bizstyle'
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_logo = '_static/sarra_horror_culture.jpg'

html_theme_options = { 'sidebar_span': 6 }
