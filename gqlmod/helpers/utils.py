import graphql

__all__ = 'unwrap_type', 'walk_query', 'walk_variables'


def unwrap_type(node):
    """
    Gets the true type node from an schema node.

    Returns the list of wrappers, the real type first and the outermost last
    """
    rv = [node]

    while isinstance(node, graphql.GraphQLWrappingType):
        node = node.of_type
        rv.append(node)

    return list(reversed(rv))


def unwrap_type_node(node):
    """
    Gets the true type node from an AST node.

    Returns the list of wrappers, the real type first and the outermost last
    """
    rv = []

    while True:
        rv.append(node)
        if isinstance(node, graphql.NonNullTypeNode):
            node = node.type
            continue
        elif isinstance(node, graphql.ListTypeNode):
            node = node.type
            continue
        else:
            break

    return list(reversed(rv))


def get_schema_fields(snode):
    # Start unwrapping
    if isinstance(snode, graphql.GraphQLField):
        snode = snode.type
    elif isinstance(snode, graphql.GraphQLInputField):
        snode = snode.type
    snode, *_ = unwrap_type(snode)
    if isinstance(snode, graphql.GraphQLScalarType):  # Is subclass of GraphQLNamedType
        return {}
    elif isinstance(snode, graphql.GraphQLEnumType):  # Is subclass of GraphQLNamedType
        return {}
    elif isinstance(snode, graphql.GraphQLNamedType):
        return snode.fields
    else:
        raise TypeError(f"Dunno how to get the fields for {snode!r}")


def walk_query_node(path, qnode, snode, schema):
    for qfield in qnode.selection_set.selections:
        if isinstance(qfield, graphql.InlineFragmentNode):
            # Nothing to do on this field, just populate stuff for the recursion
            type_name = qfield.type_condition.name.value
            sfield = schema.get_type(type_name)
            fpath = path
        elif isinstance(qfield, graphql.FieldNode):
            name = qfield.name.value
            fpath = path + (name,)
            sfield = get_schema_fields(snode)[name]
            yield fpath, qfield, sfield
        else:
            raise TypeError(f"Can't handle a {type(qfield)} ({qfield!r})")
        if qfield.selection_set:
            yield from walk_query_node(fpath, qfield, sfield, schema)


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

    yield from walk_query_node((), query_ast, root, schema)


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

        typ, *_ = unwrap_type_node(var.type)
        if isinstance(typ, graphql.GraphQLScalarType):
            continue
        elif typ.kind == 'named_type':
            pass
        else:
            raise TypeError(f"Can't get type for {var!r} ({typ!r})")

        tname = typ.name.value
        real_type = schema.get_type(tname)

        yield from walk_schema_node((name,), real_type)
