##############################################################################
#    Copyright (C) 2001, 2002, 2003 Lalo Martins <lalo@laranja.org>,
#                  and Contributors

#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307, USA
""" compiler - separated in its own module as it does not need Zope to run """

i18n_ns = 'http://xml.zope.org/namespaces/tal/i18n'

from pax.backwards_compatibility import *

# special marker (we're using 0 because it's pickle-friendly)
_no_domain = 0

class I18nCompiler(object):
    '''The domain attribute is stored in each element; this results in lexical
    domain scope, which results in better i18n/metal interaction'''
    def __init__(self):
        self.name = 'i18n'
        self.ns = i18n_ns

    def initialize(self, context):
        context.i18n_domain_stack = [None]

    def __call__(self, element, context):
        domain = element.attributes[i18n_ns].get('domain', _no_domain)
        context.i18n_domain_stack.append(domain)
        if domain is _no_domain:
            domain = [d for d in context.i18n_domain_stack if d is not _no_domain][-1]
        element.i18n_domain = domain
        return element

    def postprocess(self, element, context):
        context.i18n_domain_stack.pop()
        return element

i18n_compiler = I18nCompiler()
