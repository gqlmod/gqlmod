"""
Allows importing .gql files as Python modules, tied into the rest of the
library.
"""
import ast

import graphql
from import_x import ExtensionLoader

from ._mod_impl import __query__
from .providers import query_for_schema


def build_func(provider, definition):
    """
    Builds a python function from a GraphQL AST definition
    """
    name = definition.name.value
    source = graphql.print_ast(definition)
    assert definition.operation != graphql.OperationType.SUBSCRIPTION
    params = [build_param(var) for var in definition.variable_definitions]
    # TODO: Line numbers
    return ast.FunctionDef(
        name=name,
        args=ast.arguments(
            args=[],
            defaults=[],
            kwonlyargs=[ast.arg(arg=name, annotation=None) for name, _ in params],
            kw_defaults=[val for _, val in params],
            vararg=None,
            kwarg=None,
        ),
        body=[
            ast.Return(
                value=ast.Call(
                    func=ast.Name(id='__query__', ctx=ast.Load()),
                    args=[
                        value2pyliteral(provider),
                        value2pyliteral(source),

                    ],
                    keywords=[
                        ast.keyword(arg=name, value=ast.Name(id=name, ctx=ast.Load()))
                        for name, _ in params
                    ],
                ),
            ),
        ],
        decorator_list=[],
    )


def build_param(var):
    name = var.variable.name.value
    # NOTE: Don't care about the type name until we can start building annotations
    if var.type.kind == 'non_null_type':
        # typ = var.type.type.name.value
        nullable = False
    elif var.type.kind == 'named_type':
        # typ = var.type.name.value
        nullable = True
    has_default = nullable or (var.default_value is not None)
    defaultvalue = gqlliteral2value(var.default_value)
    return name, value2pyliteral(defaultvalue) if has_default else None


def value2pyliteral(val):
    if isinstance(val, int):
        return ast.Num(n=val)
    elif isinstance(val, float):
        return ast.Num(n=val)
    elif isinstance(val, str):
        return ast.Str(s=val)
    elif val is None:
        return ast.NameConstant(value=None)
    else:
        raise ValueError(f"Can't translate {val!r}")


def gqlliteral2value(node):
    if node is None:
        return None
    return graphql.value_from_ast_untyped(node)


class GqlLoader(ExtensionLoader):
    extension = '.gql'
    auto_enable = True

    @staticmethod
    def handle_module(module, path):
        with open(path, 'rt', encoding='utf-8') as fobj:
            provider, code = read_code(fobj)
        gast = graphql.parse(graphql.Source(code, path))

        if provider is not None:
            schema = query_for_schema(provider)
            errors = graphql.validate(schema, gast)
            if errors:
                raise find_first_error(errors)
        else:
            raise RuntimeError(f"No provider defined in {module.__name__}")

        mod = ast.Module(body=[
            build_func(provider, defin)
            for defin in gast.definitions
            if defin.kind == 'operation_definition'
        ])
        ast.fix_missing_locations(mod)

        module.__query__ = __query__
        code = compile(mod, path, 'exec')
        exec(code, vars(module))


def read_code(fobj):
    provider = None
    # Provider is "#~provider~", ignoring whitespace, and most be in an initial
    # block of #'s
    for line in fobj:
        line = line.strip().replace(' ', '').replace('\t', '')
        if line.startswith('#~') and line.endswith('~'):
            provider = line[2:-1]
            break
        elif not line.startswith('#'):
            break

    fobj.seek(0)
    return provider, fobj.read()


def find_first_error(errors):
    locmap = {
        loc: err
        for err in errors
        for loc in err.locations
    }
    locs = sorted(locmap.keys(), key=lambda l: (l.line, l.column))
    return locmap[locs[0]]
