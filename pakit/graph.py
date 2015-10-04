"""
Simple graph implementation.
Uses a dictionary of adjacency lists for edge management.
"""
from __future__ import absolute_import

from pakit.exc import CycleInGraphError


class DiGraph(object):
    """
    Repesents a directed graph with adjacency lists.

    Attributes:
        adj_lists: Dictionary that maps vertex name onto adjacent vertices
                  stored in a list.
        visited: Dictionary that maps vertex name onto simple boolean.
    """
    def __init__(self):
        self.adj_lists = {}

    def __str__(self):
        msg = ['There are ' + str(self.num_verts) + ' vertices.']
        msg += ['The adjacency lists are:']
        msg += ['  ' + key + ': ' + ', '.join(sorted(self.adj_lists[key]))
                for key in sorted(self.adj_lists)]
        return '\n' + '\n'.join(msg)

    def __contains__(self, key):
        """
        True iff the key name is in the adj_lists dictionary.
        """
        return key in self.adj_lists

    @property
    def num_verts(self):
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
    Topological sort of graph.
    Side Effect: Empties the graph.

    Returns:
        A list in sorted order.

    Raises:
        CycleInGraphError: The directed graph had a cycle.
    """
    t_list = []
    last_len = graph.num_verts

    while graph.num_verts:
        for key in graph.adj_lists:
            if graph.adj_lists[key] == []:
                t_list.append(key)
                graph.remove(key)
                break

        if last_len == graph.num_verts:
            raise CycleInGraphError(str(graph))
        last_len = graph.num_verts

    return t_list
