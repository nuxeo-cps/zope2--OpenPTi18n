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
""" handle the i18n: namespace """

from pax.backwards_compatibility import *
from pax.paxtransform import AttributeHandler, StopTransform
from pax import XML, Literal
import zLOG, sys
from Products.PageTemplates.GlobalTranslationService import getGlobalTranslationService
from types import TupleType, StringType, UnicodeType
from i18n_compiler import i18n_ns

default_domain = 'default'

class translate_wrapper:
    "Call translators that don't accept the 7th argument"
    def __init__(self, translate):
        self.translate = translate
        
    def __call__(self, domain, msgid, data, request, target, default):
        res = self.translate(domain, msgid, data, request, target)
        if res is None or res is msgid:
            return default
        return res

class I18nHandler(object):
    def __init__(self):
        self.name = 'i18n'
        self.ns = i18n_ns

    def initialize(self, context):
        context.i18n_info_stack = []
        context.i18n_domain_stack = [None]
        context.i18n_name_stack = [{}]
        context.translate = getGlobalTranslationService().translate
        if context.translate.func_code.co_nlocals == 6:
            context.translate = translate_wrapper(context.translate)
        self.ns_map = getattr(context, 'root_xmlns_map', None)

    def __call__(self, element, context):
        context.i18n_info_stack.append(element.attributes[i18n_ns])
        domain = getattr(element, 'i18n_domain', context.i18n_domain_stack[-1])
        context.i18n_domain_stack.append(domain)
        context.i18n_name_stack.append({})
        return element

    def postprocess(self, element, context):
        # this one does the real work
        # this is done on postprocess and not in a transform to better interact
        # with tal:replace, tal:omit-tag, etc
        info = context.i18n_info_stack.pop()
        domain = context.i18n_domain_stack.pop() or default_domain
        names = context.i18n_name_stack.pop()
        request = context.global_vars['request']
        if not element or type(element) is TupleType:
            # oops - we have been removed, probably by tal:condition: bail out
            return element
        try:
            del element.attributes[i18n_ns]
        except:
            pass
        #FIXME: domain is TALES?
        if info.has_key('translate') or info.has_key('attributes'):
            if info.has_key('target'):
                target = context.evaluate(info['target'])
            else:
                target = None
        if info.has_key('translate'):
            msgid = info['translate']
            if hasattr(element, 'children'):
                default = XML(element.children, self.ns_map)
            else:
                default = XML(element, self.ns_map)
            default = ' '.join(default.split())
            if msgid == '':
                msgid = default
            if info.has_key('data'):
                data = context.evaluate(info['data']).replace('_', '-').lower()
            elif names:
                data = names
            else:
                data = None
            result = Literal(context.translate(domain, msgid, data,
                                               request, target, default))
            if hasattr(element, 'children'):
                element.children = [result]
            else:
                element = result
        if info.has_key('attributes') and hasattr(element, 'attributes'):
            attrs = element.attributes.setdefault(element.ns, {})
            for name in info['attributes'].split(';'):
                attr = name.strip().split()
                if len(attr) == 1:
                    msgid = attrs[name]
                elif len(attr) == 2:
                    name, msgid = attr
                else: # old-style
                    for name in attr:
                        msgid = attrs[name]
                        attrs[name] = context.translate(domain, msgid, None, request, target, msgid)
                    msgid = name = None
                if msgid is not None:
                    attrs[name] = context.translate(domain, msgid, None, request, target, msgid)
        if info.has_key('name'):
            name = info['name']
            element = context.tr_engine.postprocess(element, context)
            context.i18n_name_stack[-1][name] = element
            element = u'${%s}' % name
        return element

i18n_handler = I18nHandler()
