"""
brew.py
~~~~~~~
brew py is brew formula generator for the deadlinks package

"""
from typing import (Dict, Tuple, Optional, List) #pylint: disable-msg=W0611

from textwrap import dedent

import requests
from jinja2 import Template
import json

try:
    from packaging.version import parse
except ImportError:
    from pip._vendor.packaging.version import parse

template = Template(
    dedent(
        """\
        class {{class}} < Formula
          include Language::Python::Virtualenv

          desc "{{description}}"
          homepage "{{homepage}}"
          url "{{url}}"
          sha256 "{{digest}}"

          depends_on "python"
        {% for package in packages %}
          resource "{{ package[0] }}" do
            url "{{ package[2] }}"
            sha256 "{{ package[1] }}"
          end
        {% endfor %}
          def install
            virtualenv_install_with_resources
          end

          test do
            # version assertion
            assert_match /#{version}/, shell_output("#{bin}/deadlinks --version")

            # deaddomain expected result
            (testpath/"localhost.localdomain.log").write <<~EOS
              ===========================================================================
              URL=<http://localhost.localdomain>; External Checks=Off; Threads=1; Retry=0
              ===========================================================================
              Links Total: 1; Found: 0; Not Found: 1; Ignored: 0; Redirects: 0
              ---------------------------------------------------------------------------\e[?25h
              [ failed ] http://localhost.localdomain
            EOS

            # deaddomain assertion
            output = shell_output("deadlinks localhost.localdomain --no-progress --no-colors")
            assert_equal (testpath/"localhost.localdomain.log").read, output
          end
        end"""))


def build_formula(app, requirements) -> str:

    data = {
        'class': app['app_package'][0].upper() + app['app_package'][1:],
        'description': app['description'][:-1],
        'homepage': app['app_website'],
        'packages': [],
    }

    data['url'], data['digest'] = info(app['app_package'], "", "")

    for _package in requirements:
        pkg, cmp, version = clean_version(_package)
        url, digest = info(pkg, cmp, version)
        data['packages'].append((pkg, digest, url))

    return template.render(**data)


def clean_version(package) -> Tuple[str, str, str]:
    """ Splits the module from requirments to the tuple: (pkg, cmp_op, ver) """

    separators = ["==", ">=", "<=", "!="]
    for s in separators:
        if s in package:
            return package.partition(s)

    return (package, "", "")


def info(pkg, cmp: Optional[str], version: Optional[str]) -> Tuple[str, str]:
    """ Return version of package on pypi.python.org using json. """

    package_info = 'https://pypi.python.org/pypi/{}/json'.format(pkg)
    req = requests.get(package_info)

    if req.status_code != requests.codes.ok:
        raise RuntimeError("Can't request PiPy")

    j = json.loads(req.text)
    releases = j.get('releases', {})
    versions = releases.keys()
    version = release(versions, cmp, version)

    source = lambda x: x.get("python_version") == "source"
    version = list(filter(source, releases[str(version)]))[0]

    return version['url'], version["digests"]['sha256']


def release(releases, pkg_cmp, pkg_ver):
    """ filter available release to pick one included in formula """

    not_prerelease = lambda x: not x.is_prerelease

    cmps = {
        '!=': lambda x: x != parse(pkg_ver),
        '==': lambda x: x == parse(pkg_ver),
        '>=': lambda x: x >= parse(pkg_ver),
        '<=': lambda x: x <= parse(pkg_ver),
    }

    _versions = list(releases)
    _versions = map(parse, releases)
    _versions = filter(not_prerelease, _versions)

    if pkg_cmp and pkg_ver:
        _versions = filter(cmps[pkg_cmp], _versions)

    versions = sorted(_versions, reverse=True)
    if not versions:
        raise RuntimeError("No matching version found")

    return versions[0]
