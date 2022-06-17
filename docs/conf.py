# -- Project information -----------------------------------------------------

project = "Debutizer"
copyright = "2021, Tyler Compton"
author = "Tyler Compton"

release = "0.13.0"


# -- General configuration ---------------------------------------------------

extensions = []

templates_path = ["_templates"]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_logo = "_static/logo.svg"

html_static_path = ["_static"]
html_css_files = [
    "custom.css",
]
