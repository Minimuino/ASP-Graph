# -*- coding: utf-8 -*-

import pygraphviz as pgv

def show_graph(m):
    A = pgv.AGraph()
    A.node_attr['shape'] = 'none'
    A.node_attr['font'] = 'Roboto'
    A.node_attr['fontsize'] = 16

    for a in m.atoms():
        A.add_node(a)

    A.layout('dot')
    A.draw('##graphviz-output##.png')
    print "Wrote ##graphviz-output##"
