"""
Allows importing .gql files as Python modules, tied into the rest of the
library.
"""
import ast
import sys

import graphql
from import_x import ExtensionLoader

from . import _mod_impl
from .errors import MissingProviderError, from_graphql_validate
from .providers import query_for_schema, get_additional_kwargs
from .helpers.types import annotate


def build_func(provider, definition, schema, is_async):
    """
    Builds a python function from a GraphQL AST definition
    """
    name = definition.name.value
    source = graphql.print_ast(definition)
    assert definition.operation != graphql.OperationType.SUBSCRIPTION
    params = [build_param(var) for var in definition.variable_definitions]
    query_func = '__aquery__' if is_async else '__query__'

    # TODO: Line numbers

    if sys.version_info >= (3, 8):
        py38 = {
            'posonlyargs': [],
        }
    else:
        py38 = {}

    return ast.FunctionDef(
        name=name,
        args=ast.arguments(
            args=[],
            defaults=[],
            kwonlyargs=[ast.arg(arg=name, annotation=None) for name, _ in params],
            kw_defaults=[val for _, val in params],
            vararg=None,
            kwarg=None,
            **py38
        ),
        body=[
            ast.Return(
                value=ast.Call(
                    func=ast.Name(id=query_func, ctx=ast.Load()),
                    args=[
                        value2pyliteral(provider),
                        value2pyliteral(source),

                    ],
                    keywords=[
                        ast.keyword(arg=name, value=ast.Name(id=name, ctx=ast.Load()))
                        for name, _ in params
                    ] + [
                        ast.keyword(arg=name, value=(
                            val if isinstance(val, ast.AST) else value2pyliteral(val)
                        ))
                        for name, val in get_additional_kwargs(provider, definition, schema).items()
                    ],
                ),
            ),
        ],
        decorator_list=[],
    )


def build_param(var):
    name = var.variable.name.value

    # TODO: How to handle lists?
    nullable = (var.type.kind != 'non_null_type')

    has_default = nullable or (var.default_value is not None)
    defaultvalue = gqlliteral2value(var.default_value)
    return name, value2pyliteral(defaultvalue) if has_default else None


def value2pyliteral(val):  # noqa: C901
    """
    Transforms a python value into a literal in AST form.
    """
    if val is None:
        return ast.NameConstant(value=None)
    elif val is ...:
        return ast.Ellipsis()
    elif val is True:
        return ast.NameConstant(value=True)
    elif val is False:
        return ast.NameConstant(value=False)
    elif isinstance(val, int):
        return ast.Num(n=val)
    elif isinstance(val, float):
        return ast.Num(n=val)
    elif isinstance(val, str):
        return ast.Str(s=val)
    elif isinstance(val, bytes):
        return ast.Bytes(s=val)
    elif isinstance(val, tuple):
        return ast.Tuple(elts=[value2pyliteral(item) for item in val])
    elif isinstance(val, list):
        return ast.List(elts=[value2pyliteral(item) for item in val])
    elif isinstance(val, dict):
        return ast.Dict(
            # .keys() and .values() have been documented to return things in the
            # same order since Py2
            keys=[value2pyliteral(item) for item in val.keys()],
            values=[value2pyliteral(item) for item in val.values()],
        )
    elif isinstance(val, set):
        return ast.Set(elts=[value2pyliteral(item) for item in val])
    else:
        raise ValueError(f"Can't translate {val!r} into a literal")


def gqlliteral2value(node):
    """
    Transforms a GraphQL query AST into a python value.
    """
    if node is None:
        return None
    return graphql.value_from_ast_untyped(node)


def load_and_validate(path, fobj=None):
    if fobj is None:
        with open(path, 'rt', encoding='utf-8') as fobj:
            provider, code, has_code = read_code(fobj)
    else:
        provider, code, has_code = read_code(fobj)

    # graphql can't handle empty files
    if has_code:
        gast = graphql.parse(graphql.Source(code, path))
    else:
        gast = graphql.language.DocumentNode(definitions=[])

    if provider is None:
        # FIXME: Lump this with above
        raise MissingProviderError(path)

    schema = query_for_schema(provider)
    errors = graphql.validate(schema, gast)

    if not errors:
        # Just automatically compute type and ref annotations. We'll probably need it.
        annotate(gast, schema)

    return provider, gast, schema, errors


class GqlLoader(ExtensionLoader):
    extension = '.gql'
    auto_enable = True

    @classmethod
    def find_spec(cls, fullname, path, *p, **kw):
        """Return the spec of the module."""

        if fullname.endswith('_async'):
            fullname = fullname[:-len('_async')]
            suffix = '_async'
        elif fullname.endswith('_sync'):
            fullname = fullname[:-len('_sync')]
            suffix = '_sync'
        else:
            suffix = ''

        spec = super().find_spec(fullname, path, *p, **kw)
        if spec is not None:
            spec.name += suffix
        return spec

    @staticmethod
    def handle_module(module, path):
        is_async = False
        if module.__name__.endswith('_async'):
            is_async = True
        elif module.__name__.endswith('_sync'):
            is_async = False

        provider, gast, schema, errors = load_and_validate(path)
        if errors:
            raise from_graphql_validate(errors)

        if sys.version_info >= (3, 8):
            py38 = {
                'type_ignores': [],
            }
        else:
            py38 = {}

        mod = ast.Module(body=[
            build_func(provider, defin, schema, is_async)
            for defin in gast.definitions
            if defin.kind == 'operation_definition'
        ], **py38)
        ast.fix_missing_locations(mod)

        module.__builtins__ = _mod_impl
        code = compile(mod, path, 'exec')
        exec(code, vars(module))


def read_code(fobj):
    provider = None
    # Provider is "#~provider~", ignoring whitespace, and must be in an initial
    # block of #'s
    loc = 0
    for line in fobj:
        line = line.strip().replace(' ', '').replace('\t', '')
        if line.startswith('#~') and line.endswith('~'):
            provider = line[2:-1]
            break
        elif not line.startswith('#'):
            loc += bool(line)
            break

    # Count the remaining LOCs
    for line in fobj:
        line = line.strip().replace(' ', '').replace('\t', '')
        if line:
            loc += 1

    fobj.seek(0)
    return provider, fobj.read(), bool(loc)


def scan_file(path, fobj=None):
    _, _, _, errors = load_and_validate(path, fobj)
    yield from errors
