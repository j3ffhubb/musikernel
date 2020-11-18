# -*- coding: utf-8 -*-
#
import sys, os

sys.path.insert(0, os.path.abspath('..'))

#extensions = ['sphinx.ext.autodoc', 'sphinxcontrib.fulltoc']
extensions = ['sphinx.ext.autodoc']

templates_path = ['templates']
html_theme_path = ['theme']
exclude_patterns = ['build']

source_suffix = '.rst'
master_doc = 'index'

project = u'pyliblo'
copyright = u'2007-2014, Dominic Sacré'
version = '0.10.0'
release = ''

html_theme = 'nasophon'
html_copy_source = False
pygments_style = 'sphinx'

add_module_names = False
autodoc_member_order = 'bysource'
autodoc_default_flags = ['members', 'undoc-members']


from sphinx.ext.autodoc import py_ext_sig_re
from sphinx.util.docstrings import prepare_docstring
from sphinx.domains.python import PyClassmember, PyObject, py_sig_re


def process_docstring(app, what, name, obj, options, lines):
    """
    Remove leading function signatures from docstring.
    """
    while len(lines) and py_ext_sig_re.match(lines[0]) is not None:
        del lines[0]

def process_signature(app, what, name, obj,
                      options, signature, return_annotation):
    """
    Replace function signature with those specified in the docstring.
    """
    if hasattr(obj, '__doc__') and obj.__doc__ is not None:
        lines = prepare_docstring(obj.__doc__)
        siglines = []

        for line in lines:
            if py_ext_sig_re.match(line) is not None:
                siglines.append(line)
            else:
                break

        if len(siglines):
            siglines[0] = siglines[0][siglines[0].index('('):]
            return ('\n'.join(siglines), None)

    return (signature, return_annotation)


# monkey-patch PyClassmember.handle_signature() to replace __init__
# with the class name.
handle_signature_orig = PyClassmember.handle_signature
def handle_signature(self, sig, signode):
    if '__init__' in sig:
        m = py_sig_re.match(sig)
        name_prefix, name, arglist, retann = m.groups()
        sig = sig.replace('__init__', name_prefix[:-1])
    return handle_signature_orig(self, sig, signode)
PyClassmember.handle_signature = handle_signature


# prevent exception fields from collapsing
PyObject.doc_field_types[2].can_collapse = False


def setup(app):
    app.connect('autodoc-process-docstring', process_docstring)
    app.connect('autodoc-process-signature', process_signature)
