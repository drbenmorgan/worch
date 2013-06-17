#!/usr/bin/env python
'''
Package specific interpretation layered on deconf.
'''

import os
import deconf
from subprocess import check_output, CalledProcessError

def ups_flavor():
    '''
    Ow, my balls.
    '''
    kern, host, rel, vend, mach = os.uname()
    if mach in ['x86_64','sun','ppc64']:
        mach = '64bit'
    else:
        mach = ''
    rel = '.'.join(rel.split('.')[:2])
    libc = check_output(['ldd','--version']).split('\n')[0].split()[-1]
    return '%s%s+%s-%s' % (kern, mach, rel, libc)

def host_description():
    '''
    Return a dictionary of host description variables.
    '''
    ret = {}
    uname_fields = ['kernelname', 'hostname', 
                    'kernelversion', 'vendorstring', 'machine']
    uname = os.uname()
    for k,v in zip(uname_fields, uname):
        ret[k] = v
    platform = '{kernelname}-{machine}'.format(**ret)
    ret['platform'] = platform
    try:
        flavor = check_output(['ups','flavor'])
    except OSError:
        flavor = ups_flavor()
    ret['ups_flavor'] = flavor

    ret['gcc_dumpversion'] = check_output(['gcc','-dumpversion']).strip()
    ret['gcc_dumpmachine'] = check_output(['gcc','-dumpmachine']).strip()
    try:
        ma = check_output(['gcc','-print-multiarch']).strip() # debian-specific
    except CalledProcessError:
        ma = ""
    ret['gcc_multiarch'] = ma
    ret['libc_version'] = check_output(['ldd','--version']).split('\n')[0].split()[-1]

    return ret


class PkgFormatter(object):
    def __init__(self, **kwds):
        self.vars = host_description()
        self.vars.update(kwds)

    def __call__(self, string, **kwds):
        if not string: return string
        tags = kwds.get('tags')
        if tags:
            tags = [x.strip() for x in tags.split(',')]
            kwds.setdefault('tagsdashed',  '-'.join(tags))
            kwds.setdefault('tagsunderscore', '_'.join(tags))

        version = kwds.get('version')
        if version:
            kwds.setdefault('version_2digit', '.'.join(version.split('.')[:2]))
            kwds.setdefault('version_underscore', version.replace('.','_'))
            kwds.setdefault('version_nodots', version.replace('.',''))
        vars = dict(self.vars)
        vars.update(kwds)
        ret = string.format(**vars)

        # print 'formatting "%s" with:' %string
        # from pprint import PrettyPrinter
        # pp = PrettyPrinter(indent=2)
        # pp.pprint(vars)
        # print 'got: "%s"' % ret
        return ret


def load(filename, start='start', formatter = None, **kwds):
    if not formatter:
        formatter = PkgFormatter()
    suite = deconf.load(filename, start=start, formatter=formatter, **kwds)
    
    # post-process
    install_dirs = {}
    for group in suite['groups']:
        for package in group['packages']:
            pkgname = package['package']
            install_dir = package['install_dir']
            install_dirs['%s_install_dir'%pkgname] = install_dir

    for group in suite['groups']:
        to_replace = []
        for package in group['packages']:
            new = deconf.format_flat_dict(package,**install_dirs)
            to_replace.append(new)
        group['packages'] = to_replace
    return suite






# testing


def dump(filename, start='start', formatter=None):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(indent=2)

    if not formatter:
        prefix ='/tmp/simple'
        formatter = PkgFormatter(prefix=prefix, PREFIX=prefix)
    data = load(filename, start=start, formatter=formatter)

    print 'Starting from "%s"' % start
    pp.pprint(data)

if '__main__' == __name__:
    import sys
    dump(sys.argv[1:])