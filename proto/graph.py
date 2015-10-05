"""
Simple graph implementation.
I am experimenting before putting it into pakit.

Adjacency list makes sense due to sparse nature of package
dependencies & python support for lists.
"""
from __future__ import absolute_import, print_function


class CycleInGraphError(Exception):
    """
    There was a cycle in the graph.
    """
    pass


class Vertex(object):
    """
    A simple vertex object.
    """
    def __init__(self, name):
        self.name = name
        self.was_visited = False

    def __str__(self):
        return self.name + ' was visited: ' + str(self.was_visited)


class DiGraph(object):
    """
    Repesents a directed graph with adjacency lists.

    Attributes:
        adj_list: Dictionary that maps vertex name onto adjacent vertices
                  stored in a list.
        verts: Dictionary that maps vertex names onto booleans.
               Boolean tracks if node visited for some algs.
    """
    def __init__(self):
        self.adj_list = {}
        self.verts = {}

    def __str__(self):
        msg = ['The vertex list has: ' + str(self.num_verts) + ' elements.']
        msg += sorted(self.verts.keys())
        msg += ['The adjacency list is:']
        msg += ['{0}: {1}'.format(key, ', '.join(self.adj_list[key])) for key
                in sorted(self.adj_list)]
        return '\n '.join(msg)

    def __contains__(self, key):
        """
        True iff the key is present in the verts dictionary.
        """
        return key in self.verts

    @property
    def num_verts(self):
        """
        The number of vertices in the graph.
        """
        return len(self.verts)

    def add_vertex(self, key):
        """
        Add a vertex to the graph, optionally with data.
        """
        self.verts[key] = False
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

    def get_unvisited_adjacent(self, key):
        """
        Get first position connected to key that has NOT
        been visited before.

        Returns:
            A position of a vertex in verts, else None if not found.
        """
        for adj_key in self.adj_list[key]:
            if not self.verts[adj_key]:
                return adj_key

        return None

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
            del self.verts[key]
            del self.adj_list[key]
        except KeyError:
            pass
        for adj_key in self.adj_list:
            try:
                self.adj_list[adj_key].remove(key)
            except ValueError:
                pass

    def reset_visited(self):
        """
        Reset all visited nodes to False.
        """
        for key in self.verts:
            self.verts[key] = False


class Graph(DiGraph):
    """
    An undirected graph, small changes required.
    """
    def add_edge(self, key, depends_on):
        """
        Add an edge from key to the vert depends_on

        Args:
            key: The vertex name.
            depends_on: A vertex name key depends on.
        """
        self.adj_list[key].append(depends_on)
        self.adj_list[depends_on].append(key)

    def add_edges(self, key, depends_on_all):
        """
        Add an edge from key to all verts in depends_on

        Args:
            key: The vertex name.
            depends_on: A list of vertex names key depends on.
        """
        self.adj_list[key].extend(depends_on_all)
        for dep in depends_on_all:
            self.adj_list[dep].append(key)


def bfs_search(graph, func, start_pos):
    """
    BFS Search, on unvisited nodes pass to func.

    Args:
        graph: A graph.Graph instance.
        func: A function of form func(vertex)
        start_pos: An index in the verts of graph.
    """
    queue = [start_pos]
    func(start_pos)
    graph.verts[start_pos] = True

    while len(queue):
        adjacent = graph.get_unvisited_adjacent(queue[-1])
        if adjacent:
            queue.insert(0, adjacent)
            func(adjacent)
            graph.verts[adjacent] = True
        else:
            queue.pop()


def dfs_search(graph, func, start_pos):
    """
    DFS Search, on unvisited nodes pass to func.

    Args:
        graph: A graph.Graph instance.
        func: A function of form func(vertex)
        start_pos: An index in the verts of graph.
    """
    stack = [start_pos]
    func(start_pos)
    graph.verts[start_pos] = True

    while len(stack):
        adjacent = graph.get_unvisited_adjacent(stack[-1])
        if adjacent:
            stack.append(adjacent)
            func(adjacent)
            graph.verts[adjacent] = True
        else:
            stack.pop()


def mst_search(graph, func, start_pos):
    """
    MST creation, prints edges needed for an MST.

    Args:
        graph: A graph.Graph instance.
        func: A function of form func(vertex_a, vertex_b)
        start_pos: An index in the verts of graph.
    """
    stack = [start_pos]
    graph.verts[start_pos] = True

    while len(stack):
        prev_vert = stack[-1]
        adjacent = graph.get_unvisited_adjacent(stack[-1])
        if adjacent:
            stack.append(adjacent)
            func(prev_vert, '->', adjacent)
            graph.verts[adjacent] = True
        else:
            stack.pop()


def topo_list(graph):
    """
    Topological sort of graph.

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
                print('Select:', key)
                t_list.append(key)
                graph.remove(key)
                break

        if last_len == graph.num_verts:
            print(graph)
            raise CycleInGraphError
        last_len = graph.num_verts

    return t_list


class OldGraph(object):
    """
    Repesents an undirected graph with adjacency list.
    """
    def __init__(self, max_verts):
        self.vertex_list = []
        self.adj_list = [[] for _ in range(max_verts)]

    def __str__(self):
        msg = 'The vertex list has: {0} elements\n'.format(self.num_verts)
        msg += '\n'.join([str(vert) for vert in self.vertex_list])
        msg += '\n\nThe adjacency list is:\n'
        adj_lines = [str(ind) + ': ' + ', '.join([str(num) for num in line])
                     for ind, line in enumerate(self.adj_list)]
        msg += '\n'.join(adj_lines) + '\n'
        return msg

    def __contains__(self, vert):
        return vert in [n_vert.name for n_vert in self.vertex_list]

    @property
    def num_verts(self):
        """
        Max number of verts in graph.
        """
        return len(self.vertex_list)

    def add_vertex(self, vert_name):
        """
        Add a vertex to the graph.
        """
        self.vertex_list.append(Vertex(vert_name))

    def add_edge(self, start, end):
        """
        Start and end are positional indexes into vertex list.
        """
        self.adj_list[start].append(end)
        self.adj_list[end].append(start)

    def display_vertex(self, pos):
        """
        Show a vertex at the position.
        """
        print(self.vertex_list[pos])

    def is_connected(self, start, end):
        """
        Returns true iff start has an edge to end.
        """
        return end in self.adj_list[start]

    def get_unvisited_adjacent(self, v_index):
        """
        Get first position connected to v_index that has NOT
        been visited before.

        Returns:
            A position of a vertex in vertex_list, else -1 if None found.
        """
        for pos in self.adj_list[v_index]:
            if not self.vertex_list[pos].was_visited:
                return pos

        return -1

    def remove(self, v_index):
        """
        Remove all trace of vertex at v_index.
        """
        for a_list in self.adj_list:
            try:
                a_list.remove(v_index)
            except ValueError:
                pass
        del self.adj_list[v_index]
        del self.vertex_list[v_index]
