"""Synthetic W4A starter; intentionally unimplemented, not a broken real project.

Implement the API in TASK.md. No solution, acceptance tests or oracle is included.
"""


class GraphError(ValueError):
    """An invalid graph edit or batch."""


class Planner:
    def add_node(self, name):
        return self.apply([("add_node", name)])

    def remove_node(self, name):
        return self.apply([("remove_node", name)])

    def add_dependency(self, task, prerequisite):
        return self.apply([("add_dependency", task, prerequisite)])

    def remove_dependency(self, task, prerequisite):
        return self.apply([("remove_dependency", task, prerequisite)])

    def apply(self, operations):
        raise NotImplementedError("Implement atomic graph updates")

    def nodes(self):
        raise NotImplementedError("Implement sorted node snapshots")

    def dependencies(self):
        raise NotImplementedError("Implement sorted dependency snapshots")

    def order(self):
        raise NotImplementedError("Implement deterministic topological ordering")
