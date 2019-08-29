import gqlmod  # noqa
import testmod.queries
from pprint import pprint

for name in dir(testmod.queries):
    if name.startswith('_'):
        continue
    print(name, repr(getattr(testmod.queries, name)))

print("")

pprint(testmod.queries.HeroNameAndFriends())
