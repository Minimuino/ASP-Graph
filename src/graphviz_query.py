# -*- coding: utf-8 -*-

# Copyright (C) 2017 Carlos Pérez Ramil <c.pramil at udc.es>

# This file is part of ASP-Graph.

# ASP-Graph is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# ASP-Graph is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with ASP-Graph.  If not, see <http://www.gnu.org/licenses/>.

import pygraphviz as pgv

def show_graph(m):
    A = pgv.AGraph()
    A.node_attr['shape'] = 'none'
    A.node_attr['font'] = 'Roboto'
    A.node_attr['fontsize'] = 16

    for a in m.atoms():
        A.add_node(a)

    # Possible values: neato, dot, twopi, circo, fdp, nop, wc, acyclic,
    # gvpr, gvcolor, ccomps, sccmap, tred, sfdp.
    A.layout('neato')
    A.draw('##graphviz-output##.png')
    print "Wrote ##graphviz-output##"
