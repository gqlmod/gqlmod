Tool Usage
==========

In addition the module, several tools are available.

``gqlmod`` command
------------------

Included in the package is a ``gqlmod`` tool. This provides static analysis
functionality outside of your software.

``gqlmod check``
~~~~~~~~~~~~~~~~

Checks graphql files for syntax and schema validty. Unlike importing, all
findable errors are reported.

Give the list of files to check, or pass `--search` to scan the current
directory (recursively).

GitHub Action
-------------

The check function is also available as a GitHub Action (with extra annotation
integration).

.. code-block:: yaml
    :caption: .github/workflows/gqlmod.yml

    name: gqlmod check

    on: push

    jobs:
      check:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v1
            with:
              fetch-depth: 1
          - uses: gqlmod/check-action@master
            with:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

You do need to use the ``actions/checkout`` action before calling ``gqlmod/check-action``, and the ``GITHUB_TOKEN`` argument is required.
