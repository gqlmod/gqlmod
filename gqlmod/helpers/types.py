"""
Functions to help with typing of queries.
"""
import weakref

import graphql

__all__ = 'get_type', 'get_definition'

_type_annotations = weakref.WeakKeyDictionary()
_ref_annotations = weakref.WeakKeyDictionary()


def get_type(node):
    """
    Gets the schema object referenced by the given node.
    """
    try:
        return _type_annotations[node]
    except KeyError:
        pass


def get_definition(node):
    """
    Gets the AST object definining the given node
    """
    try:
        return _ref_annotations[node]
    except KeyError:
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
        _type_annotations[node] = schema

    # Explict type definitions
    def enter_named_type(self, node, key, parent, path, ancestors):
        name = node.name.value
        _type_annotations[node] = self.schema.get_type(name)

    def leave_non_null_type(self, node, key, parent, path, ancestors):
        # Copy & wrap the type from the inner
        t = get_type(node.type)
        assert t is not None
        _type_annotations[node] = graphql.GraphQLNonNull(t)

    def leave_list_type(self, node, key, parent, path, ancestors):
        # Copy & wrap the type from the inner
        t = get_type(node.type)
        assert t is not None
        _type_annotations[node] = graphql.GraphQLList(t)

    # Fields
    def enter_field(self, node, key, parent, path, ancestors):
        # Find the parent type, and then find our type on that.
        for p in reversed([*ancestors, parent]):
            # This should go until we find a field or operation definition
            parent_schema = get_type(p)
            if parent_schema is not None:
                break
        assert isinstance(parent_schema, graphql.GraphQLNamedType)
        _type_annotations[node] = _type_annotations[node.selection_set] = \
            parent_schema.fields[node.name.value]

    def enter_argument(self, node, key, parent, path, ancestors):
        # Find the parent type, and then find our type on that.
        for p in reversed([*ancestors, parent]):
            # This should go until we find a field
            parent_schema = get_type(p)
            if parent_schema is not None:
                break
        assert isinstance(parent_schema, graphql.GraphQLField)
        _type_annotations[node] = _type_annotations[node.value] = \
            parent_schema.args[node.name.value]

    def enter_object_field(self, node, key, parent, path, ancestors):
        # Find the parent type, and then find our type on that.
        for p in reversed([*ancestors, parent]):
            # This should go until we find a object_value
            parent_schema = get_type(p)
            if parent_schema is not None:
                break
        assert isinstance(parent_schema, graphql.GraphQLNamedType)
        _type_annotations[node] = _type_annotations[node.selection_set] = \
            parent_schema.fields[node.name.value]

    # Variables
    def exit_variable_definition(self, node, key, parent, path, ancestors):
        # Copy from the type
        t = get_type(node.type)
        assert t is not None
        _type_annotations[node] = t

    # Literals
    def enter_object_value(self, node, key, parent, path, ancestors):
        # Confirm that we got our type from our parent
        assert get_type(node) is not None

    def enter_int_value(self, node, key, parent, path, ancestors):
        # Confirm nothing hinky is going on
        t = get_type(node)
        assert t == self.schema.get_type('Int')
        _type_annotations[node] = self.schema.get_type('Int')

    def enter_float_value(self, node, key, parent, path, ancestors):
        # Confirm nothing hinky is going on
        t = get_type(node)
        assert t == self.schema.get_type('Float')
        _type_annotations[node] = self.schema.get_type('Float')

    def enter_string_value(self, node, key, parent, path, ancestors):
        # Confirm nothing hinky is going on
        t = get_type(node)
        assert t == self.schema.get_type('String')
        _type_annotations[node] = self.schema.get_type('String')

    def enter_boolean_value(self, node, key, parent, path, ancestors):
        # Confirm nothing hinky is going on
        t = get_type(node)
        assert t == self.schema.get_type('Boolean')
        _type_annotations[node] = self.schema.get_type('Boolean')

    def enter_list_value(self, node, key, parent, path, ancestors):
        # Copy our type to the kids
        schema = get_type(node)
        assert schema is not None
        for child in node.values:
            _type_annotations[child] = schema.of_type

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
        _ref_annotations[node] = self.scope[node.name.value]

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

        _ref_annotations[node] = defi


def annotate(ast, schema):
    """
    Scans the AST and builds type information from the schema
    """
    graphql.visit(ast, RefAnnotationVisitor())
    graphql.visit(ast, TypeAnnotationVisitor(schema))
