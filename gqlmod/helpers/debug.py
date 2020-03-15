import graphql

__all__ = 'debug_ast', 'repr_node'


def repr_node(obj):
    attrs = ' '.join(
        f"{name}={getattr(obj, name)}"
        for name in obj.keys
        if name != 'loc'
    )
    return f"{obj.kind}@{obj.loc} {attrs}"


class DebugVisitor(graphql.Visitor):
    depth = 0
    indent = "  "

    def enter(self, node, key, parent, path, ancestors):
        print(f"{self.indent * self.depth}{repr_node(node)}")
        self.depth += 1

    def leave(self, node, key, parent, path, ancestors):
        self.depth -= 1


def debug_ast(node):
    graphql.visit(node, DebugVisitor())
