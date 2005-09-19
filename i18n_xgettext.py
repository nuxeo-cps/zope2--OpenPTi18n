#!/usr/bin/python
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

'''%(name)s

Given one or more files with i18n: directives in the command line,
it collects explicit message and builds a potfile.

If one of these is a directory, recursively traverse it for files
with matching filename.

You can use the -f, --filenames option to tell it what is a
"matching filename". It defaults to "%(filenames)s". The value
is interpreted as a regular expresion.

You can specify the output file with -o, --output. It defaults to
standard output.

You can specify to use the default string as the translation with
-d or --use-defaults.
'''

import sys, types, os, re, pax, pax.paxtransform, traceback, time
from pax.backwards_compatibility import *
from i18n_compiler import i18n_ns
from OpenTAL import tal_handler

# filename regexpr
# Nuxeo
# Do not treat files which start with "." such as Emacs ".#xxx" swap files.
filenames=r'^[^.].+\.z?pt$'
# how many references to show
example_max = 8
# timezone to show in the header
timezone = '%02d%02d' % (int(time.timezone/3600), int(time.timezone/60)%60)
if time.timezone >= 0:
    timezone = '+' + timezone

# header for potfiles
potfile_header = r'''
# Gettext Message File for %(domain)s.
# Your Name <your@email>, Year
msgid ""
msgstr ""
"Project-Id-Version: %(domain)s\n"
"POT-Creation-Date: %(timestamp)s%(domain)s\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: Your Name <your@email>\n"
"Language-Team: Name <email>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=ISO-8859-15\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=1; plural=0;\n"
"Language-Code: en\n"
"Language-Name: English\n"
"Preferred-encodings: latin9 utf-8\n"
"Domain: %(domain)s\n"

'''[1:]

# other pax-related variables
tal_ns = tal_handler.ns
namespaces = {'i18n': i18n_ns, tal_handler.name: tal_ns}

if __name__ == '__main__':
    name = sys.argv[0]
else:
    name = __name__

__doc__ = __doc__ % locals()


class Named_substitution(object):
    renderer = pax.Element()
    def __init__(self, name, tal):
        self.name = name
        self.tal = tal

    def __xml__(self, ns_map):
        #ugh
        if self.tal and not ns_map.has_key(' omit tal'):
            return u'${%s (tal%s)}' % (
                self.name,
                self.renderer.__attribute_ns_xml__(tal_ns, self.tal, {}))
        return u'${%s}' % self.name

class i18n_id_collector(object):
    def __init__(self):
        self.name = 'i18n'
        self.ns = i18n_ns

    def initialize(self, context):
        context.ns_map = {}

    def __call__(self, element, context):
        for prefix, uri in element.nsdecls.items():
            context.ns_map[uri] = prefix
        for prefix, id in element.lame_namespaces.items():
            context.ns_map[id] = prefix
        return element

    def postprocess(self, element, context):
        name = element.attributes[i18n_ns].get('name', None)
        msgid = element.attributes[i18n_ns].get('translate', None)
        # Nuxeo
        attributes = element.attributes[i18n_ns].get('attributes', None)
        main_attributes = element.attributes.get(element.ns, {})
        tal = element.attributes.get(tal_ns, {})
        tal_attributes = tal.get('attributes', '').split()
        del element.attributes[i18n_ns]
        ns_map_hack = context.ns_map.copy()
        ns_map_hack[' omit tal'] = 1
        if hasattr(element, 'children'):
            default = pax.XML(element.children, ns_map_hack)
        else:
            default = pax.XML(element, ns_map_hack)

        default = ' '.join(default.split())
        xml = pax.XML(element, context.ns_map)
        if msgid:
            context.register(msgid, xml, default)
        elif msgid == "":
            if default:                 # Nuxeo
                context.register(default, xml, default)
            # else msgid is dynamic - don't mess with it
        # Nuxeo
        if attributes is not None:
            for aname in attributes.split(';'):
                aname = aname.strip()
                if aname in tal_attributes:
                    # msgid is dynamic - don't mess with it
                    continue
                value = main_attributes.get(aname, None)
                if value is None:
                    raise ProcessError, 'i18n:attributes on inexistent attribute at ' + xml
                context.register(value, xml, value)
        if name:
            return Named_substitution(name, tal)
        return element


_engine = pax.paxtransform.Engine()
_engine.add_handler(i18n_id_collector())


class MessageCatalog(object):
    def __init__(self):
        self.filename = None
        self.items = {}
        self.had_errors = 0

    def set_filename(self, filename):
        self.filename = filename

    def register(self, msgid, example, default=None):
        info = self.filename, example, default
        try:
            self.items[msgid].append(info)
        except KeyError:
            self.items[msgid] = [info]

    def dump(self, fileobj=sys.stdout, use_default=None):
        fileobj.write(potfile_header)

        ids = self.items.keys()
        ids.sort()
        w = fileobj.write
        for msgid in ids:
            examples_used = []
            last_filename = None
            info = self.items[msgid]
            for filename, example, default in info[:example_max]:
                if filename is not last_filename:
                    w('\n#: from ')
                    w(filename)
                if example not in examples_used:
                    w('\n#.   '.join([''] + example.split('\n')))
                    examples_used.append(example)
            remain = len(info) - example_max
            if remain > 0:
                w('\n#: %s more references' % remain)
            w('\nmsgid "')
            w(msgid.replace('"', r'\"'))
            if not use_default:
               default = ''
            else:
               default = default or ''
               default = default.replace('"', r'\"')
            w('"\nmsgstr "%s"\n' % default)


class ProcessError(Exception): pass


def _is_multiple(it):
    try:
        for element in it:
            pass
    except:
        return False
    return not hasattr(it, 'split')


def _do_file(path, catalog):
    #__traceback_info__ = path
    try:
        tree = pax.text2pax(open(path).read(), namespaces)
    except:
        sys.stderr.write('\n\nError parsing %s:\n' % path)
        traceback.print_exc()
        catalog.had_errors = 1
        return
    _engine.initialize(catalog)
    catalog.set_filename(path)
    try:
        _engine.transform(tree, catalog)
    except ProcessError:
        sys.stderr.write('\n\nError parsing %s:\n' % path)
        traceback.print_exc()

def _do_dir(info, dirname, names):
    filename_re, catalog = info
    names.sort() # Nuxeo
    for name in names:
        if filename_re.search(name):
            _do_file(os.path.join(dirname, name), catalog)


def xgettext(paths, filenames=filenames, output=None, domain='default', use_default=None):
    if type(output) is types.StringType:
        # this is done first because if it raises an exception,
        # we haven't yet read potentially hundreds of files and
        # wasted a lot of time
        output = open(output, 'w')
    catalog = MessageCatalog()
    filename_re = re.compile(filenames)
    if not _is_multiple(paths):
        paths = (paths,)
    for path in paths:
        if os.path.isdir(path):
            os.path.walk(path, _do_dir, (filename_re, catalog))
        else:
            _do_file(path, catalog)
    catalog.dump(output, use_default)
    if catalog.had_errors:
        raise ProcessError


if __name__ == '__main__':
    def _help():
        print __doc__

    import getopt
    try:
        opts, paths = getopt.getopt(sys.argv[1:],
                                   'f:ho:dD:',
                                   'filenames= help output= use-default domain='.split())
    except getopt.GetoptError, e:
        print e.msg
        print
        _help()

    use_default = None
    output = None
    domain = 'default'
    for opt, value in opts:
        if opt in ('-f', '--filenames'):
            filenames = value
        elif opt in ('-h', '--help'):
            _help()
            sys.exit(0)
        elif opt in ('-o', '--output'):
            output = value
        elif opt in ('-d', '--use-default'):
            use_default = 1
        elif opt in ('-D', '--domain'):
            domain = value
    if output is None:
        output = domain + '.pot'

    potfile_header = potfile_header % {
        'timestamp':time.strftime('%Y-%m-%d %H:%M', time.localtime()),
        'tz':timezone,
        'domain':domain}

    try:
        xgettext(paths, filenames, output, domain, use_default)
    except ProcessError:
        import traceback
        traceback.print_exc()
        sys.exit(1)
