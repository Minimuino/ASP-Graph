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
import gringo

import normalization as norm
from name_manager import NameManager

class Solver(object):
    """Wrapper class for POTASSCO.

    It works as a high-level interface to Clingo, and it has 3 main functions:

    * Reducing an Equilibrium Logic first-order formula into a safe Logic
      Program (if possible). Using the normalization module.
    * Making queries to Clingo and retrieving a set of Stable Models.
      Using the gringo module.
    * Generating an Equilibrium Graph from the set of Stable Models.
      Using the pygraphviz module.
    """

    def __init__(self, **kwargs):
        self.solver = gringo.Control()
        self.formula = None
        self.constants = {}
        self.stable_models = []

    def _reset_solver(self):
        self.solver = gringo.Control()
        self.solver.conf.solve.models = 0

    def get_models(self):
        return tuple(self.stable_models)

    def set_formula(self, rpn_formula, constants={}):
        self.formula = norm.Formula(rpn_formula)
        self.constants = constants
        self.stable_models = []

    def solve(self, show=[]):
        self._reset_solver()

        n = self.formula.root
        n.replace_constants(self.constants)
        print 80 * '-'
        print 'RPN formula constants removed:\n', self.constants, '\n', n
        n = norm.pnf(n)
        print 80 * '-'
        print 'Prenex RPN formula:\n', n
        print 80 * '-'

        m = norm.get_matrix(n)
        for i in norm.normalization(m):
            s = norm.to_asp(i)
            print 'ASP RULE: ', s
            self.solver.add('base', [], s)
        for s in show:
            self.solver.add('base', [], s)

        self.solver.ground([('base', [])])
        print 80 * '-'
        print 'Stable models:'
        result = self.solver.solve(on_model=self.on_model)
        retstr = 'Undefined'
        if result == gringo.SolveResult.UNKNOWN:
            retstr = 'UNKNOWN'
        elif result == gringo.SolveResult.SAT:
            retstr = 'SAT'
        elif result == gringo.SolveResult.UNSAT:
            retstr = 'UNSAT'
        print retstr
        return retstr

    def on_model(self, m):
        self.stable_models.append(str(m))
        print m

    def parse_model(self, m):
        # Dict used to translate from arg position to anchor position
        anchor_codes = ['w', 'e', 'n', 's']
        nm = NameManager.Instance()

        # nodes = {1: 'label1', 2: 'label2', ...}
        # edges = [(1, 2, 'e'), ...]
        nodes = {}
        edges = []
        predicates = m.split()
        for n, p in enumerate(predicates):
            parts = p.split('(')
            atom = parts[0]
            terms = parts[1] if len(parts) > 1 else []
            nodes[n] = atom
            if terms:
                terms = [t.strip(' )') for t in terms.split(',')]
                atom_anchors = nm.get(atom).hook_points
                term_anchors = [a for i, a in enumerate(anchor_codes)
                                if atom_anchors[i]]
                assert len(terms) == len(term_anchors)
                for i, t in enumerate(terms):
                    nodes[t] = t
                    edges.append((n, t, term_anchors[i]))
        return nodes, edges

    def generate_graph(self, m):
        A = pgv.AGraph()
        A.graph_attr['size'] = (10, 10)
        A.graph_attr['pad'] = 1
        A.graph_attr['splines'] = 'spline'
        A.graph_attr['overlap'] = 'false'
        A.node_attr['shape'] = 'none'
        A.node_attr['font'] = 'Roboto'
        A.node_attr['fontsize'] = 16
        A.node_attr['width'] = 0
        A.node_attr['height'] = 0

        nodes, edges = self.parse_model(m)
        print 'Nodes:'
        for n in nodes:
            A.add_node(n, label=nodes[n])
            print n, 'label=', nodes[n]
        print 'Edges:'
        for e in edges:
            A.add_edge(e[0], e[1], tailport=e[2])
            print e[0], ':', e[2], '--', e[1]

        # Possible values: neato, dot, twopi, circo, fdp, nop, wc, acyclic,
        # gvpr, gvcolor, ccomps, sccmap, tred, sfdp.
        A.layout('dot')
        A.draw('##graphviz-output##.png')
        print "Wrote ##graphviz-output##.png"
