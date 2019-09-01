Importable GraphQL modules
==========================

[![Documentation Status](https://readthedocs.org/projects/gqlmod/badge/?version=master)](https://gqlmod.readthedocs.io/)

`gqlmod` allows you to keep your GraphQL queries in `.gql` files and import them
as modules.

* Validation of queries at import time
* Validation of queries against the schema

Usage
-----

Install both `gqlmod` and any providers you need. (The `starwars` provider ships
with `gqlmod`, so you can begin playing with it immediately.)

Define a `.gql` file with your queries and mutations, like so:

```graphql
#~starwars~

query HeroForEpisode($ep: Episode!) {
  hero(episode: $ep) {
    name
    ... on Droid {
      primaryFunction
    }
    ... on Human {
      homePlanet
    }
  }
}
```

And then you can just import it and use it:

```python
import gqlmod  # noqa
from mygql import HeroForEpisode

print(HeroForEpisode(ep='JEDI'))
```


Why
---

So why use this?

* Strong validation as soon as possible (when the modules are imported)
* All the work is done at warmup, not when the query is made
* I think not mixing languages produces cleaner code?
