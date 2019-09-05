import graphql

__all__ = 'unwrap_type', 'walk_query', 'walk_variables', 'ScalarToJsonHelper'


def unwrap_type(node):
    """
    Gets the true type.

    Returns the list of wrappers, the real type first and the outermost last
    """
    rv = [node]

    while isinstance(node, graphql.GraphQLWrappingType):
        node = node.of_type
        rv.append(node)

    return list(reversed(rv))


def get_schema_fields(snode):
    # Start unwrapping
    if isinstance(snode, graphql.GraphQLField):
        snode = snode.type
    snode, *_ = unwrap_type(snode)
    if isinstance(snode, graphql.GraphQLNamedType):
        return snode.fields
    elif isinstance(snode, graphql.GraphQLScalarType):
        return {}
    else:
        raise TypeError(f"Dunno how to get the fields for {snode!r}")


def walk_query_node(path, qnode, snode):
    for qfield in qnode.selection_set.selections:
        name = qfield.name.value
        fpath = path + (name,)
        sfield = get_schema_fields(snode)[name]
        yield fpath, qfield, sfield
        if qfield.selection_set:
            yield from walk_query_node(fpath, qfield, sfield)


def walk_schema_node(path, snode):
    for name, field in get_schema_fields(snode).items():
        fpath = path + (name,)
        yield fpath, field
        yield from walk_schema_node(fpath, field)


def walk_query(query_ast, schema):
    """
    Walks a query (by AST), generating 3-tuples of:

    * the name path (Tuple[str])
    * the AST node of the field in the query (:py:class:`graphql.language.ast.FieldNode`)
    * the schema node of the field (:py:class:`graphql.type.definition.GraphQLField`)
    """
    if query_ast.operation == graphql.OperationType.QUERY:
        root = schema.query_type
    elif query_ast.operation == graphql.OperationType.MUTATION:
        root = schema.mutation_type
    elif query_ast.operation == graphql.OperationType.SUBSCRIPTION:
        root = schema.subscription_type

    yield from walk_query_node((), query_ast, root)


def walk_variables(query_ast, schema):
    """
    Walks the variables (by AST), generating 2-tuples of:

    * the name path (Tuple[str])
    * the schema node of the field (:py:class:`graphql.type.definition.GraphQLField`)

    Note that the paths are rooted in the name of the variable, but the variable
    itself is not produced.
    """
    for var in query_ast.variable_definitions:
        name = var.variable.name.value

        typ = var.type
        if typ.kind == 'non_null_type':
            typ = typ.type
        if isinstance(typ, graphql.GraphQLScalarType):
            continue
        elif typ.kind == 'named_type':
            pass
        else:
            raise TypeError(f"Can't get type for {var!r}")

        yield from walk_schema_node((name,), typ)


class ScalarToJsonHelper:
    """
    Helps with custom scalars and conversion to/from JSON forms
    """

    def __init__(self, type_tree):
        ...

    def to_json(self, data):
        ...

    def from_json(self, data):
        ...
