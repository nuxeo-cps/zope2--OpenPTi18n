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
__version__ = '''
$Id$
'''.strip()

from i18n_handler import i18n_handler
from i18n_compiler import i18n_compiler

def initialize(context):
    # plug into Zope AltPT
    #from Products.OpenPT.ZOPT import register_handlers
    #register_handlers(i18n_handler, i18n_compiler, 0)
    try:
        from Products.OpenPT.FSOPT import FSPageTemplate
    except ImportError:
        pass
    #FSPageTemplate.handlers = ('i18n',) + FSPageTemplate.handlers
