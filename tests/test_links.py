"""
links_test.py
--------------

Links object test coverage
"""

# pylint: disable=redefined-outer-name

import pytest

from deadlinks import (Link, URL)


@pytest.fixture(scope="module")
def link():
    """ Return valid config object. """
    return Link("https://google.com")


@pytest.mark.parametrize(
    'base, url, expected',
    [
        (
            "http://localhost:1313/documentation/",
            "part1.html",
            "http://localhost:1313/documentation/part1.html",
        ),
        (
            "http://localhost:1313/documentation",
            "part1.html",
            "http://localhost:1313/part1.html",
        ),
        (
            "http://localhost:1313/documentation",
            "../part1.html",
            "http://localhost:1313/part1.html",
        ),
        (
            "http://localhost:1313/documentation/",
            "../part1.html",
            "http://localhost:1313/part1.html",
        ),
    ],
)
def test_url_link(base, url, expected):
    """ Relative link generation. """
    assert Link(base).link(url) == expected


@pytest.mark.parametrize(
    'base, url',
    [
        ("http://localhost:1313/", "http://localhost:3000/"),
        ("http://google.com/", "http://bing.com/"),
        ("http://google.com/", "http://google.com.ua/"),
        ("http://google.com.ua/", "http://google.com"),
        ("http://google.com/", "http://ww1.google.com"),
        ("http://ww1.google.com/", "http://www.www.google.com"),
    ],
)
def test_is_external(base, url):
    """ External links. """

    assert Link(base).is_external(URL(url))
    assert Link(url).is_external(URL(base))
    assert Link(base).is_external(Link(url))
    assert Link(url).is_external(Link(base))
    assert Link(base).is_external(url)
    assert Link(url).is_external(base)


@pytest.mark.parametrize(
    'base, url', [*[
        ("http://localhost:1313/", 2222),
        ("http://localhost:1313/", 2222.1),
    ]])
def test_is_external_of_wrong_type(base, url):
    """ (Mis)Typed external links """

    with pytest.raises(TypeError):
        assert Link(base).is_external(url)


@pytest.mark.parametrize(
    'base, url',
    [
        ("http://www.google.com/", "http://google.com"),
        ("http://www.www.google.com/", "http://www.www.google.com"),
        ("http://www.google.com/", "http://google.com:80"),
        ("https://www.google.com/", "https://google.com:443"),
        ("https://www.google.com:443/", "https://google.com"),
    ],
)
def test_is_interal_links(base, url):
    """ Are this links internal to url? """

    assert not Link(base).is_external(url)
    assert not Link(url).is_external(base)
    assert not Link(base).is_external(URL(url))
    assert not Link(url).is_external(URL(base))


def test_links(server):
    """ General testing for link. """

    from tests.helpers import Page

    url = server.router({
        '^/$': Page('<a href="https://google.com/">google</a>').exists(),
    })

    l = Link(url)

    assert l.exists()
    assert len(l.links) == 1
    assert str(l) == url
    assert l.url() == url


@pytest.mark.parametrize(
    "url",
    [
        "localhost", # no scheme
        "http://localhost:4040404", # no existsing domain
        "http://:4040404", # no existsing domain
    ],
)
def test_bad_links(url):
    assert not Link(url).exists()


@pytest.fixture(scope="function")
def ignore_domains():
    """ Fixture for domains """
    return ["github.com"]


@pytest.fixture(scope="function")
def ignore_pathes():
    """ Fixture for pathes. """
    return ["issues/new", "edit/master", "commit"]


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/kubeflow/website/issues/new?title",
        "https://github.com/kubeflow/website/commit/d26bed8d8",
        "https://github.com/kubeflow/website/edit/master/content/docs/",
    ],
)
def test_ignored(ignore_domains, ignore_pathes, url):
    """ Ignored domains and pathes matching. """

    assert Link(url).match_domains(ignore_domains)
    assert Link(url).match_pathes(ignore_pathes)


@pytest.mark.parametrize("url", [
    "https://google.com",
    "http://github.com",
])
def test_is_valid(url):
    """ Tests URL for valid (for crawler) format. """
    assert Link(url).is_valid()


def test_eq():
    """ Compare two objects. """

    assert Link("http://google.com") == Link("http://google.com")
    assert Link("http://google.com") == "http://google.com"
    assert "http://google.com" == Link("http://google.com")

    with pytest.raises(TypeError):
        Link('http://google.com') == 1 # pylint: disable=expression-not-assigned


def test_refferer():
    """ Test referrer. """

    l = Link("https://made.ua")
    refferer = "https://google.com"
    l.add_referrer(refferer)
    l.add_referrer(refferer)

    assert refferer in l.get_referrers()


def test_match_domain():
    """ Domain matching. """

    l = Link("https://made.ua")
    assert l.match_domains(["made.ua"])
    assert not l.match_domains(["google.com"])


def test_link_existance():
    """ Link existance. """

    l = Link("http://asdasdasa/")
    assert not l.exists()
    assert "Failed to establish a new connection" in l.message
    assert len(l.links) == 0