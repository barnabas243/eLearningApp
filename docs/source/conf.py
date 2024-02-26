# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import django

# Add the directory containing your Django apps to the Python path
sys.path.insert(0, os.path.abspath('/home/barnabas243/projects/endterm/eLearningApp/'))

# Initialize Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'eLearningApp.settings'
django.setup()

# -- Project information -----------------------------------------------------
project = 'eLearningApp'
copyright = '2024, Tan Tian Fong Barnabas'
author = 'Tan Tian Fong Barnabas'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx_copybutton',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
]
templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
