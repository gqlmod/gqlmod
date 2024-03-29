import testmod.queries
from pprint import pprint

for name in dir(testmod.queries):
    if name.startswith('_'):
        continue
    print(name, repr(getattr(testmod.queries, name)))

qnames = {name for name in dir(testmod.queries) if not name.startswith('_')}
assert qnames == {'Hero', 'HeroForEpisode', 'HeroNameAndFriends'}
assert all(callable(getattr(testmod.queries, name)) for name in qnames)

print("")

data = testmod.queries.HeroNameAndFriends()
pprint(data)

assert data == {
    'hero': {'friends': [{'name': 'Luke Skywalker'},
                         {'name': 'Han Solo'},
                         {'name': 'Leia Organa'}],
             'name': 'R2-D2'}}
