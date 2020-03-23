"""
Functions to help with typing of queries.
"""

import graphql

__all__ = 'get_type', 'get_schema', 'get_definition', 'annotate'

SCHEMA_ATTR = '__schema'  # The schema object that provides the definition of this node
DEF_ATTR = '__def'  # The query object that provides the definition of this node (variables, fragments)


def get_schema(node):
    """
    Gets the schema definition of the given ast node.
    """
    try:
        return getattr(node, SCHEMA_ATTR)
    except AttributeError:
        return


def get_type(node, *, unwrap=False):
    """
    Gets the schema type of the given ast node.

    If unwrap is true, also remove any wrapping types.
    """
    qltype = get_schema(node)
    if isinstance(qltype, graphql.GraphQLField):
        qltype = qltype.type

    if unwrap:
        qltype = graphql.get_named_type(qltype)

    return qltype


def get_definition(node):
    """
    Gets the AST object definining the given node.

    Like, a Variable node will point to a variable definition.
    """
    try:
        return getattr(node, DEF_ATTR)
    except AttributeError:
        pass


class TypeAnnotationVisitor(graphql.Visitor):
    """
    Query visitor to add type annotations.
    """
    def __init__(self, schema):
        self.schema = schema

    # types:
    # enter: named_type, field, argument, object_value, object_field
    # leave: non_null_type, list_type, variable_definition

    # Top-levels (which are subsets of schema objects)
    def enter_operation_definition(self, node, key, parent, path, ancestors):
        if node.operation == graphql.OperationType.QUERY:
            schema = self.schema.query_type
        elif node.operation == graphql.OperationType.MUTATION:
            schema = self.schema.mutation_type
        elif node.operation == graphql.OperationType.SUBSCRIPTION:
            schema = self.schema.subscription_type
        setattr(node, SCHEMA_ATTR, schema)

    def leave_fragment_definition(self, node, key, parent, path, ancestors):
        # Copy type from the type
        t = get_type(node.type_condition)
        assert t is not None
        setattr(node, SCHEMA_ATTR, t)

    def apply_inline_fragment(self, node):
        t = get_type(node.type_condition)
        setattr(node, SCHEMA_ATTR, t)
        setattr(node.selection_set, SCHEMA_ATTR, t)

    # Explict type definitions
    def enter_named_type(self, node, key, parent, path, ancestors):
        name = node.name.value
        node_type = self.schema.get_type(name)
        setattr(node, SCHEMA_ATTR, node_type)
        self._type_parent(node, parent)

    def leave_non_null_type(self, node, key, parent, path, ancestors):
        # Copy & wrap the type from the inner
        t = get_type(node.type)
        assert t is not None
        setattr(node, SCHEMA_ATTR, graphql.GraphQLNonNull(t))
        self._type_parent(node, parent)

    def leave_list_type(self, node, key, parent, path, ancestors):
        # Copy & wrap the type from the inner
        t = get_type(node.type)
        assert t is not None
        setattr(node, SCHEMA_ATTR, graphql.GraphQLList(t))
        self._type_parent(node, parent)

    def _type_parent(self, node, parent):
        if isinstance(parent, graphql.InlineFragmentNode):
            self.apply_inline_fragment(parent)

        if isinstance(parent, graphql.VariableDefinitionNode):
            self.apply_variable_definition(parent)

    # Directives
    def enter_directive(self, node, key, parent, path, ancestors):
        name = node.name.value
        node_type = self.schema.get_directive(name)
        setattr(node, SCHEMA_ATTR, node_type)

    # Fields
    def enter_field(self, node, key, parent, path, ancestors):
        if node.name.value == '__typename':
            # Special name
            node_schema = graphql.GraphQLNonNull(graphql.self.schema.get_type('String'))
        else:
            # Find the parent type, and then find our type on that.
            for p in reversed([*ancestors, parent]):
                # This should go until we find a field, operation definition, inline fragment, ...
                parent_schema = get_type(p, unwrap=True)
                if parent_schema is not None:
                    break
            assert isinstance(parent_schema, graphql.GraphQLNamedType)

            try:
                node_schema = parent_schema.fields[node.name.value]
            except KeyError:
                raise ValueError(f"Could not find {node.name.value} in the fields of {parent_schema.name}; this may be a validation error")
        setattr(node, SCHEMA_ATTR, node_schema)
        if node.selection_set is not None:
            setattr(node.selection_set, SCHEMA_ATTR, node_schema)

    def enter_argument(self, node, key, parent, path, ancestors):
        # Find the parent type, and then find our type on that.
        for p in reversed([*ancestors, parent]):
            # This should go until we find a field or directive
            try:
                parent_schema = getattr(p, SCHEMA_ATTR)
            except AttributeError:
                continue
            else:
                break
        assert isinstance(parent_schema, (graphql.GraphQLField, graphql.GraphQLDirective))

        node_schema = parent_schema.args[node.name.value]
        setattr(node, SCHEMA_ATTR, node_schema)
        setattr(node.value, SCHEMA_ATTR, node_schema.type)

    def enter_object_field(self, node, key, parent, path, ancestors):
        # Find the parent type, and then find our type on that.
        for p in reversed([*ancestors, parent]):
            # This should go until we find a object_value
            parent_schema = get_type(p, unwrap=True)
            if parent_schema is not None:
                break

        assert isinstance(parent_schema, graphql.GraphQLNamedType)

        node_schema = parent_schema.fields[node.name.value]
        setattr(node, SCHEMA_ATTR, node_schema)
        setattr(node.value, SCHEMA_ATTR, node_schema.type)

    # Variables
    def apply_variable_definition(self, node):
        # Copy from the type
        t = get_type(node.type)
        assert t is not None
        setattr(node, SCHEMA_ATTR, t)
        if node.default_value:
            setattr(node.default_value, SCHEMA_ATTR, t)

    # Literals
    def enter_object_value(self, node, key, parent, path, ancestors):
        # Confirm that we got our type from our parent
        assert get_type(node) is not None

    def enter_int_value(self, node, key, parent, path, ancestors):
        # Confirm nothing hinky is going on
        t = get_type(node)
        assert graphql.get_named_type(t) == self.schema.get_type('Int')
        setattr(node, SCHEMA_ATTR, self.schema.get_type('Int'))

    def enter_float_value(self, node, key, parent, path, ancestors):
        # Confirm nothing hinky is going on
        t = get_type(node)
        assert graphql.get_named_type(t) == self.schema.get_type('Float')
        setattr(node, SCHEMA_ATTR, self.schema.get_type('Float'))

    def enter_string_value(self, node, key, parent, path, ancestors):
        # Confirm nothing hinky is going on
        t = get_type(node)
        assert graphql.get_named_type(t) == self.schema.get_type('String')
        setattr(node, SCHEMA_ATTR, self.schema.get_type('String'))

    def enter_boolean_value(self, node, key, parent, path, ancestors):
        # Confirm nothing hinky is going on
        t = get_type(node)
        assert graphql.get_named_type(t) == self.schema.get_type('Boolean')
        setattr(node, SCHEMA_ATTR, self.schema.get_type('Boolean'))

    def enter_list_value(self, node, key, parent, path, ancestors):
        # Copy our type to the kids
        schema = get_type(node)
        assert schema is not None
        assert isinstance(schema, graphql.GraphQLList)
        for child in node.values:
            setattr(child, SCHEMA_ATTR, schema.of_type)

    def enter_variable(self, node, key, parent, path, ancestors):
        # TODO: Check the type given to us matches the declared type
        ...


class RefAnnotationVisitor(graphql.Visitor):
    def __init__(self):
        # A believe only a single scope can be active
        self.scope = None

    def enter_operation_definition(self, node, key, parent, path, ancestors):
        assert self.scope is None
        self.scope = {
            vardef.variable.name.value: vardef
            for vardef in node.variable_definitions
        }

    def leave_operation_definition(self, node, key, parent, path, ancestors):
        assert self.scope is not None
        self.scope = None

    def enter_variable(self, node, key, parent, path, ancestors):
        assert self.scope is not None
        setattr(node, DEF_ATTR, self.scope[node.name.value])

    def enter_fragment_spread(self, node, key, parent, path, ancestors):
        # Find the document
        for doc in reversed(ancestors):
            if getattr(doc, 'kind') == 'document':
                break
        else:
            return

        # Find the fragment
        for defi in doc.definitions:
            if defi.kind == 'fragment_definition' and defi.name.value == node.name.value:
                break
        else:
            return

        setattr(node, DEF_ATTR, defi)


def annotate(ast, schema):
    """
    Scans the AST and builds type information from the schema
    """
    graphql.visit(ast, RefAnnotationVisitor())
    graphql.visit(ast, TypeAnnotationVisitor(schema))
