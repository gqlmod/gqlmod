import pytest

import gqlmod.enable  # noqa


def test_names():
    import testmod.queries
    qnames = {name for name in dir(testmod.queries) if not name.startswith('_')}
    assert qnames == {'Hero', 'HeroForEpisode', 'HeroNameAndFriends'}
    assert all(callable(getattr(testmod.queries, name)) for name in qnames)


def test_data_sync():
    import testmod.queries_sync
    result = testmod.queries_sync.HeroNameAndFriends()
    assert not result.errors
    assert result.data == {
        'hero': {'friends': [{'name': 'Luke Skywalker'},
                             {'name': 'Han Solo'},
                             {'name': 'Leia Organa'}],
                 'name': 'R2-D2'}}


@pytest.mark.asyncio
async def test_data_async():
    import testmod.queries_async
    result = await testmod.queries_async.HeroNameAndFriends()
    assert not result.errors
    assert result.data == {
        'hero': {'friends': [{'name': 'Luke Skywalker'},
                             {'name': 'Han Solo'},
                             {'name': 'Leia Organa'}],
                 'name': 'R2-D2'}}


def test_random_import():
    # Import a random stdlib module that nobody should use
    import imaplib  # noqa    


def test_imports():
    import testmod.queries as q
    import testmod.queries_sync as qs
    import testmod.queries_async as qa

    assert q.__file__ == qs.__file__ == qa.__file__
    assert q is not qs is not qa
