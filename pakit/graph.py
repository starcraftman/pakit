"""
Implements graph logic for dependencies between Recipes.

DiGraph: A directed graph with adjacency lists.
topological_sort: Order vertices to meet edge dependencies.
"""
from __future__ import absolute_import

from pakit.exc import CycleInGraphError


class DiGraph(object):
    """
    Repesents a directed graph with adjacency lists.

    Attributes:
        adj_lists: Dictionary that maps vertex name onto adjacent vertices
                  stored in a list.
    """
    def __init__(self):
        self.adj_lists = {}

    def __str__(self):
        msg = ['There are ' + str(self.size) + ' vertices.']
        msg += ['The adjacency lists are:']
        msg += ['  ' + key + ': ' + ', '.join(sorted(self.adj_lists[key]))
                for key in sorted(self.adj_lists)]
        return '\n' + '\n'.join(msg)

    def __contains__(self, key):
        """
        True iff the key name is in the adj_lists dictionary.
        """
        return key in self.adj_lists

    def __len__(self):
        return self.size

    @property
    def size(self):
        """
        The number of vertices in the graph.
        """
        return len(self.adj_lists)

    def add_edge(self, key, depends_on):
        """
        Add an edge from key to the vert depends_on

        Args:
            key: The vertex name.
            depends_on: A vertex name key depends on.
        """
        self.adj_lists[key].append(depends_on)

    def add_edges(self, key, depends_on_all):
        """
        Add an edge from key to all verts in depends_on_all.

        Args:
            key: The vertex name.
            depends_on: A list of vertex names key depends on.
        """
        self.adj_lists[key].extend(depends_on_all)

    def add_vertex(self, key):
        """
        Add a vertex to the graph.
        """
        self.adj_lists[key] = []

    def is_connected(self, start, end):
        """
        Returns true iff start has an edge to end.
        """
        return end in self.adj_lists[start]

    def remove(self, key):
        """
        Remove a vertex from the graph.
        Delete it from all adjacency lists as well.
        """
        try:
            del self.adj_lists[key]
        except KeyError:
            pass
        for adj_list in self.adj_lists.values():
            while adj_list.count(key):
                adj_list.remove(key)


def topological_sort(graph):
    """
    Generate a topological sort of a graph.
    Side Effect: Empties the graph.

    Returns:
        A node in the graph with requirements satisfied.

    Raises:
        CycleInGraphError: The directed graph has a cycle.
    """
    last_len = graph.size

    while graph.size:
        for key in graph.adj_lists:
            if graph.adj_lists[key] == []:
                graph.remove(key)
                yield key
                break

        if last_len == graph.size:
            raise CycleInGraphError(str(graph))
        last_len = graph.size
