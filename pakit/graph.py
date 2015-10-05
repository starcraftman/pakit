"""
Simple graph implementation.
Uses a dictionary of adjacency lists for easy management.
"""
from __future__ import absolute_import, print_function


class CycleInGraphError(Exception):
    """
    There was a cycle in the graph.
    """
    pass


class DiGraph(object):
    """
    Repesents a directed graph with adjacency lists.

    Attributes:
        adj_list: Dictionary that maps vertex name onto adjacent vertices
                  stored in a list.
    """
    def __init__(self):
        self.adj_list = {}

    def __str__(self):
        msg = ['The vertex list has: ' + str(self.num_verts) + ' elements.']
        msg += sorted(self.adj_list.keys())
        msg += ['The adjacency list is:']
        msg += ['{0}: {1}'.format(key, ', '.join(self.adj_list[key])) for key
                in sorted(self.adj_list)]
        return '\n '.join(msg)

    def __contains__(self, key):
        """
        True iff the key name is in the adj_list dictionary.
        """
        return key in self.adj_list

    @property
    def num_verts(self):
        """
        The number of vertices in the graph.
        """
        return len(self.adj_list)

    def add_vertex(self, key):
        """
        Add a vertex to the graph.
        """
        self.adj_list[key] = []

    def add_edge(self, key, depends_on):
        """
        Add an edge from key to the vert depends_on

        Args:
            key: The vertex name.
            depends_on: A vertex name key depends on.
        """
        self.adj_list[key].append(depends_on)

    def add_edges(self, key, depends_on_all):
        """
        Add an edge from key to all verts in depends_on_all.

        Args:
            key: The vertex name.
            depends_on: A list of vertex names key depends on.
        """
        self.adj_list[key].extend(depends_on_all)

    def is_connected(self, start, end):
        """
        Returns true iff start has an edge to end.
        """
        return end in self.adj_list[start]

    def remove(self, key):
        """
        Remove a vertex from the graph.
        Delete it from all adjacency lists as well.
        """
        try:
            del self.adj_list[key]
        except KeyError:
            pass
        for adj_key in self.adj_list:
            try:
                self.adj_list[adj_key].remove(key)
            except ValueError:
                pass


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
        for key in graph.adj_list:
            if graph.adj_list[key] == []:
                t_list.append(key)
                graph.remove(key)
                break

        if last_len == graph.num_verts:
            raise CycleInGraphError(str(graph))
        last_len = graph.num_verts

    return t_list
