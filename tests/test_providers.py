from gqlmod.providers import get_provider, with_provider


def test_provider_change():
    orig = get_provider('starwars')
    with with_provider('starwars'):
        new = get_provider('starwars')
        assert orig is not new

    old = get_provider('starwars')
    assert old is orig
