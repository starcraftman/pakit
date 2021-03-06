"""
Test pakit.graph
"""
from __future__ import absolute_import, print_function
import string

from pakit.graph import DiGraph, topological_sort


class TestDiGraph(object):
    def setup(self):
        self.graph = DiGraph()

    def test__str__(self):
        self.graph.add_vertex('A')
        self.graph.add_vertex('B')
        self.graph.add_edge('A', 'B')
        print (self.graph)
        expect = [
            '',
            'There are 2 vertices.',
            'The adjacency lists are:',
            '  A: B',
            '  B: ',
        ]

        assert str(self.graph).split('\n') == expect

    def test__len__(self):
        self.graph.add_vertex('A')
        self.graph.add_vertex('B')
        assert len(self.graph) == 2

    def test_size(self):
        self.graph.add_vertex('A')
        self.graph.add_vertex('B')
        assert self.graph.size == 2

    def test_add_vertex(self):
        self.graph.add_vertex('A')
        assert 'A' in self.graph

    def test_add_edge(self):
        self.graph.add_vertex('A')
        self.graph.add_vertex('B')
        self.graph.add_edge('A', 'B')
        assert self.graph.is_connected('A', 'B')
        print(self.graph)

    def test_add_edges(self):
        self.graph.add_vertex('A')
        self.graph.add_vertex('B')
        self.graph.add_vertex('C')
        self.graph.add_edges('A', ['B', 'C'])
        assert len(self.graph.adj_lists['A']) == 2
        assert self.graph.is_connected('A', 'B')
        assert self.graph.is_connected('A', 'C')
        print(self.graph)

    def test_is_connected(self):
        self.graph.add_vertex('A')
        self.graph.add_vertex('B')
        self.graph.add_vertex('C')
        self.graph.add_edge('A', 'B')
        print(self.graph)
        assert self.graph.is_connected('A', 'B')
        assert 'B' in self.graph.adj_lists['A']
        assert not self.graph.is_connected('A', 'C')
        assert 'C' not in self.graph.adj_lists['A']

    def test_remove(self):
        self.graph.add_vertex('A')
        self.graph.add_vertex('B')
        self.graph.add_vertex('C')
        self.graph.add_edges('A', ['B', 'C'])
        print(self.graph)
        assert self.graph.size == 3
        self.graph.remove('C')
        print(self.graph)
        assert self.graph.size == 2
        assert 'C' not in self.graph
        assert self.graph.is_connected('A', 'B')
        assert not self.graph.is_connected('A', 'C')

    def test_remove_bad_key(self):
        self.graph.add_vertex('A')
        self.graph.add_vertex('B')
        self.graph.add_vertex('C')
        self.graph.add_edges('A', ['B', 'C'])
        print(self.graph)
        assert self.graph.size == 3
        self.graph.remove('D')
        print(self.graph)
        assert self.graph.size == 3


class TestTopologicalSort(object):
    def setup(self):
        max_verts = 8
        self.graph = DiGraph()
        for char in string.ascii_uppercase[0:max_verts]:
            self.graph.add_vertex(char)

        self.graph.add_edge('A', 'D')
        self.graph.add_edge('A', 'E')
        self.graph.add_edge('B', 'E')
        self.graph.add_edge('C', 'F')
        self.graph.add_edge('D', 'G')
        self.graph.add_edge('E', 'G')
        self.graph.add_edge('F', 'H')
        self.graph.add_edge('G', 'H')

    def test_topological_sort(self):
        print(self.graph)
        top_list = list(topological_sort(self.graph))
        assert len(top_list) == 8
        assert self.graph.size == 0
