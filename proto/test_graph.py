"""
Test pakit.graph
"""
from __future__ import absolute_import, print_function

import graph
import string


class TestVertex(object):
    def setup(self):
        self.vert = graph.Vertex('A')

    def test__str__(self):
        assert str(self.vert) == 'A was visited: False'

    def test_was_visited(self):
        assert not self.vert.was_visited
        self.vert.was_visited = True
        assert self.vert.was_visited


class TestUndirectedGraph(object):
    def setup(self):
        self.g = graph.Graph(10)

    def test_num_verts(self):
        self.g.add_vertex('A')
        self.g.add_vertex('B')
        assert self.g.num_verts == 2

    def test_add_vertex(self):
        self.g.add_vertex('A')
        assert 'A' in self.g

    def test_add_edge(self):
        self.g.add_vertex('A')
        self.g.add_vertex('B')
        self.g.add_edge(0, 1)
        assert self.g.is_connected(0, 1)
        assert 1 in self.g.adj_list[0]
        assert 0 in self.g.adj_list[1]

    def test_get_unvisited_adjacent(self):
        self.g.add_vertex('A')
        self.g.add_vertex('B')
        self.g.add_vertex('C')
        self.g.add_edge(0, 1)
        self.g.add_edge(0, 2)
        assert self.g.get_unvisited_adjacent(0) == 1
        self.g.vertex_list[1].was_visited = True
        assert self.g.get_unvisited_adjacent(0) == 2
        self.g.vertex_list[2].was_visited = True
        assert self.g.get_unvisited_adjacent(0) == -1

    def test_remove(self):
        self.g.add_vertex('A')
        self.g.add_vertex('B')
        self.g.add_vertex('C')
        self.g.add_edge(0, 1)
        self.g.add_edge(0, 2)
        assert self.g.num_verts == 3
        self.g.remove(2)
        assert self.g.num_verts == 2
        assert 'C' not in self.g.vertex_list


class TestSearchGraph(object):
    def setup(self):
        max_verts = 10
        self.g = graph.Graph(max_verts)
        for char in string.ascii_uppercase[0:max_verts]:
            self.g.add_vertex(char)

        self.g.add_edge(0, 1)
        self.g.add_edge(0, 2)
        self.g.add_edge(0, 3)
        self.g.add_edge(0, 4)
        self.g.add_edge(1, 5)
        self.g.add_edge(5, 7)
        self.g.add_edge(3, 6)
        self.g.add_edge(6, 8)

    def test_bfs_search(self):
        print(self.g)
        graph.bfs_search(self.g, print, 0)

    def test_dfs_search(self):
        print(self.g)
        graph.dfs_search(self.g, print, 0)


class TestMST(object):
    def setup(self):
        max_verts = 5
        self.g = graph.Graph(max_verts)
        for char in string.ascii_uppercase[0:max_verts]:
            self.g.add_vertex(char)

        self.g.add_edge(0, 1)
        self.g.add_edge(0, 2)
        self.g.add_edge(0, 3)
        self.g.add_edge(0, 4)
        self.g.add_edge(1, 2)
        self.g.add_edge(1, 3)
        self.g.add_edge(2, 3)
        self.g.add_edge(2, 4)
        self.g.add_edge(3, 4)

    def test_mst_func(self):
        print(self.g)
        graph.mst_search(self.g, print, 0)


class TestTopologicalSort(object):
    def setup(self):
        max_verts = 8
        self.g = graph.DiGraph()
        for char in string.ascii_uppercase[0:max_verts]:
            self.g.add_vertex(char)

        self.g.add_edge('A', 'D')
        self.g.add_edge('A', 'E')
        self.g.add_edge('B', 'E')
        self.g.add_edge('C', 'F')
        self.g.add_edge('D', 'G')
        self.g.add_edge('E', 'G')
        self.g.add_edge('F', 'H')
        self.g.add_edge('G', 'H')

    def test_topo_sort(self):
        print(self.g)
        expect = ['H', 'G', 'E', 'B', 'D', 'A', 'F', 'C']
        assert graph.topo_list(self.g) == expect


class TestDiGraph(object):
    def setup(self):
        self.g = graph.DiGraph()

    def test_num_verts(self):
        self.g.add_vertex('A')
        self.g.add_vertex('B')
        assert self.g.num_verts == 2

    def test_add_vertex(self):
        self.g.add_vertex('A')
        assert 'A' in self.g

    def test_add_edge(self):
        self.g.add_vertex('A')
        self.g.add_vertex('B')
        self.g.add_edge('A', 'B')
        assert self.g.is_connected('A', 'B')
        print(self.g)

    def test_is_connected(self):
        self.g.add_vertex('A')
        self.g.add_vertex('B')
        self.g.add_vertex('C')
        self.g.add_edge('A', 'B')
        print(self.g)
        assert self.g.is_connected('A', 'B')
        assert not self.g.is_connected('A', 'C')

    def test_get_unvisited_adjacent(self):
        self.g.add_vertex('A')
        self.g.add_vertex('B')
        self.g.add_vertex('C')
        self.g.add_edges('A', ['B', 'C'])
        assert self.g.get_unvisited_adjacent('A') == 'B'
        self.g.vertex_list['B'] = True
        assert self.g.get_unvisited_adjacent('A') == 'C'
        self.g.vertex_list['C'] = True
        assert self.g.get_unvisited_adjacent('A') is None

    def test_remove(self):
        self.g.add_vertex('A')
        self.g.add_vertex('B')
        self.g.add_vertex('C')
        self.g.add_edges('A', ['B', 'C'])
        print(self.g)
        assert self.g.num_verts == 3
        self.g.remove('C')
        print(self.g)
        assert self.g.num_verts == 2
        assert 'C' not in self.g
        assert self.g.is_connected('A', 'B')
        assert not self.g.is_connected('A', 'C')
