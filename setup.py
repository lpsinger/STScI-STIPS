#!/usr/bin/env python

# Licensed under a 3-clause BSD style license - see LICENSE.rst

import builtins, datetime, locale, os, pkg_resources, subprocess, sys, time, warnings

from configparser import ConfigParser

from distutils.command.build_ext import build_ext as DistutilsBuildExt
from distutils.command.sdist import sdist as DistutilsSdist

from importlib import machinery as import_machinery

from sphinx.setup_command import BuildDoc as SphinxBuildDoc

from setuptools import setup
from setuptools.config import read_configuration

# This is used by setup.py to create a new version.py - see that file for
# details. Note that the imports have to be absolute, since this is also used
# by affiliated packages.
_FROZEN_VERSION_PY_TEMPLATE = """
# Autogenerated by {packagetitle}'s setup.py on {timestamp!s} UTC

import datetime

version = "{verstr}"

major = {major}
minor = {minor}
bugfix = {bugfix}

version_info = (major, minor, bugfix)

release = {rel}
timestamp = {timestamp!r}
"""[1:]


def parse_version(version):
    p_version = pkg_resources.parse_version(version)
    if hasattr(p_version, 'base_version'):
        if p_version.base_version:
            parts = [int(part) for part in p_version.base_version.split('.')]
        else:
            parts = []
    else:
        parts = []
        for part in p_version:
            if part.startswith('*'):
                # Ignore any .dev, a, b, rc, etc.
                break
            parts.append(int(part))

    if len(parts) < 3:
        parts += [0] * (3 - len(parts))
    
    return tuple(parts[:3])


# Modified from Astropy Helpers, since having Astropy Helpers was causing
# significant difficulties.
def get_git_devstr():
    """
    Determines the number of revisions in this repository.

    Returns
    -------
    devversion : str
        Either a string with the revision number or an empty string
        if git version info could not be identified.
    """
    
    path = os.getcwd()

    cmd = ['rev-list', '--count', 'HEAD']

    try:
        stdio_encoding = locale.getdefaultlocale()[1] or 'utf-8'
    except ValueError:
        stdio_encoding = 'utf-8'

    def run_git(cmd):
        try:
            p = subprocess.Popen(['git'] + cmd, cwd=path,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE)
            stdout, stderr = p.communicate()
        except OSError as e:
            warnings.warn('Error running git: ' + str(e))
            return (None, b'', b'')

        if p.returncode == 128:
            warnings.warn('No git repository present at {0!r}! Using '
                          'default dev version.'.format(path))
            return (p.returncode, b'', b'')
        if p.returncode == 129:
            warnings.warn('Your git looks old (does it support {0}?); '
                          'consider upgrading to v1.7.2 or '
                          'later.'.format(cmd[0]))
            return (p.returncode, stdout, stderr)
        elif p.returncode != 0:
            warnings.warn('Git failed while determining revision '
                          'count: {0}'.format(_decode_stdio(stderr)))
            return (p.returncode, stdout, stderr)

        return p.returncode, stdout, stderr

    returncode, stdout, stderr = run_git(cmd)

    if returncode == 128:
        # git returns 128 if the command is not run from within a git
        # repository tree. In this case, a warning is produced above but we
        # return the default dev version of '0'.
        return '0'
    elif returncode == 129:
        # git returns 129 if a command option failed to parse; in
        # particular this could happen in git versions older than 1.7.2
        # where the --count option is not supported
        # Also use --abbrev-commit and --abbrev=0 to display the minimum
        # number of characters needed per-commit (rather than the full hash)
        cmd = ['rev-list', '--abbrev-commit', '--abbrev=0', 'HEAD']
        returncode, stdout, stderr = run_git(cmd)
        # Fall back on the old method of getting all revisions and counting
        # the lines
        if returncode == 0:
            return str(stdout.count(b'\n'))
        else:
            return ''
    else:
        return stdout.decode('utf-8').strip()


# Modified from Astropy Helpers, since having Astropy Helpers was causing
# significant difficulties.
def generate_version_py(conf):
    """
    Generate a version.py file in the package with version information, and
    update developer version strings. The package name and version are read in 
    from the ``setup.cfg`` file (from the ``name`` entry and the ``version`` 
    entry in the``[metadata]`` section).

    If the version is a developer version (of the form ``3.2.dev``), the
    version string will automatically be expanded to include a sequential
    number as a suffix (e.g. ``3.2.dev13312``), and the updated version string
    will be returned by this function.

    Based on this updated version string, a ``version.py`` file will be
    generated inside the package, containing the version string as well as more
    detailed information (for example the major, minor, and bugfix version
    numbers, a ``release`` flag indicating whether the current version is a
    stable or developer version, and so on.
    
    Parameters
    ----------
    conf : ConfigParser
        Already loaded up with `setup.cfg` data
    """

    packagename = conf.get('metadata', 'name')

    version = conf.get('metadata', 'version')
    
    release = 'dev' not in version

    if not release:
        version += get_git_devstr()
    
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH', time.time()))
    timestamp = datetime.datetime.utcfromtimestamp(epoch)
    major, minor, bugfix = parse_version(version)    

    content = _FROZEN_VERSION_PY_TEMPLATE.format(packagetitle=packagename,
                                                 timestamp=timestamp,
                                                 verstr=version,
                                                 major=major,
                                                 minor=minor,
                                                 bugfix=bugfix,
                                                 rel=release)

    with open(version_py, 'w') as f:
        # This overwrites the actual version.py
        f.write(content)
    return version


conf = ConfigParser()
conf.read('setup.cfg')

PACKAGENAME = conf.get('metadata', 'name')
version = generate_version_py(conf)

cmdclass = {
            'sdist': DistutilsSdist,
            'build_ext': DistutilsBuildExt,
            'build_docs': SphinxBuildDoc
           }

package_info = {
                'ext_modules': [],
                'packages': [],
                'package_dir': {},
                'package_data': conf['options']['package_data'],
               }

# Add the project-global data
package_info['package_data'].setdefault(PACKAGENAME, [])
package_info['package_data'][PACKAGENAME].append('data/*/*')

setup(version=version, cmdclass=cmdclass, **package_info)
