"""
tests.exporters.test_cli.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Testing cli functionality.


:copyright: (c) 2019 by Oleg Butuzov.
:license:   Apache2, see LICENSE for more details.
"""

# -- Imports -------------------------------------------------------------------

import pytest

from collections import OrderedDict

from ..helpers import Page

from deadlinks.__main__ import main

# -- Tests ---------------------------------------------------------------------


def test_options():
    """ Testing 'main' callback properties """

    assert not hasattr(main, '__click_params_groups__')
    assert hasattr(main, '_groups')
    assert isinstance(main._groups, OrderedDict)
    assert "Other" in main._groups
    assert "Default Options" in main._groups


def test_help(runner):
    """ Will check if section and main title are present in help """

    result = runner.invoke(main, ['--help'])

    assert result.exit_code == 0

    assert main.help.rstrip() in result.output

    for word in {'Usage Examples:', 'Examples', 'Other:', 'Default Options'}:
        assert word in result.output


def test_version(runner):
    """ Simple version test. """
    result = runner.invoke(main, ['--version'])

    assert result.exit_code == 0

    from deadlinks.__version__ import __app_version__ as version
    from deadlinks.__version__ import __app_package__ as package

    assert result.output.rstrip("\n") == "{}: v{}".format(package, version)


def test_default_fail_if_failed_found(server, runner):
    """ Checks general `fiff` option/ """

    # address exists, page isn't
    address = server.router({'^/$': Page("")})

    args = [address, '-s', 'none', '--no-progress']
    result = runner.invoke(main, args)

    # no fails
    assert result.exit_code == 0

    args.append("--fiff")
    result = runner.invoke(main, args)

    # failed
    assert result.exit_code == 1


@pytest.mark.parametrize('dsn', [
    "ssh://127.0.0.1:21",
    "mailto:example@example.org",
])
def test_default_dsn_with_issues(runner, dsn):
    """ Passing unsupported DSN string. """
    result = runner.invoke(main, [dsn])

    assert result.exit_code == 2
    MESSAGE = "Error: URL {} is not valid"
    assert MESSAGE.format(dsn) in result.output


def test_default_url_no_scheme_issue(server, runner):
    """ no domain cli execution test """
    address = server.router({
        '^/$': Page("").exists(),
    })

    scheme, address = address.split("//")

    args = [address, '-s', 'failed', '--no-progress', '--fiff']

    result = runner.invoke(main, args)

    assert result.exit_code == 0
    assert "{}//{}".format(scheme, address) in result.output


def test_breaking_process(server, runner):
    """ Handling SIGINT signal """

    from multiprocessing import Queue, Process
    from threading import Timer
    from time import sleep
    from os import kill, getpid
    from signal import SIGINT

    url = server.router({'^/$': Page("").slow().exists()})
    args = [url, '--no-colors', '--no-progress']

    q = Queue()

    def background():
        Timer(0.2, lambda: kill(getpid(), SIGINT)).start()
        result = runner.invoke(main, args)
        q.put(('exit_code', result.exit_code))
        q.put(('output', result.output))

    p = Process(target=background)
    p.start()

    results = {}

    while p.is_alive():
        sleep(0.1)
    else:
        while not q.empty():
            key, value = q.get()
            results[key] = value

    assert results['exit_code'] == 0
    assert "Results can be inconsistent, as execution was terminated" in results['output']
