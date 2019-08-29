import gqlmod
import testmod.queries

for name in dir(testmod.queries):
    if name.startswith('_'):
        continue
    print(name, repr(getattr(testmod.queries, name)))
