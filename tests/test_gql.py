import gqlmod
gqlmod.enable_gql_import()
import testmod.queries  # noqa


def test_names():
    qnames = {name for name in dir(testmod.queries) if not name.startswith('_')}
    assert qnames == {'Hero', 'HeroForEpisode', 'HeroNameAndFriends'}
    assert all(callable(getattr(testmod.queries, name)) for name in qnames)


def test_data():
    result = testmod.queries.HeroNameAndFriends()
    assert not result.errors
    assert result.data == {
        'hero': {'friends': [{'name': 'Luke Skywalker'},
                             {'name': 'Han Solo'},
                             {'name': 'Leia Organa'}],
                 'name': 'R2-D2'}}
