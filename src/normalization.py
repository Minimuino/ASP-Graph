# -*- coding: utf-8 -*-

"""NORMALIZATION MODULE
Transforms HT propositional formulas into logic programs with the form:
p1 & p2 & ... & pN -> q1 | q2 | ... | qM
"""

import string
import unittest

class OP:
    """Enum class for opcodes"""
    NOT = '-'
    IMPLIES = '>'
    AND = '&'
    OR = '|'

class LIT:
    """Enum class for true & false values"""
    TRUE = '/t'
    FALSE = '/f'

class Node:
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.l = left
        self.r = right

    def __eq__(self, node):
        v = False
        l = False
        r = False
        if node is None:
            return False
        if self.l:
            if self.l.__eq__(node.l):
                l = True
        else:
            if not node.l:
                l = True
        if self.r:
            if self.r.__eq__(node.r):
                r = True
        else:
            if not node.r:
                r = True
        if self.val == node.val:
            v = True
        return (v and l and r)

    def is_literal(self):
        if ((self.val == OP.NOT) or (self.val == OP.IMPLIES)
            or (self.val == OP.AND) or (self.val == OP.OR)):
            return False
        else:
            return True

    def print_tree(self, n):
        if self.r:
            self.r.print_tree(n+1)
        print ' '*2*n, self.val
        if self.l:
            self.l.print_tree(n+1)

    def get_string(self):
        string = ''
        if self.l:
            string += self.l.get_string()
        string += self.val
        if self.r:
            string += self.r.get_string()
        return string

class Formula:

    separator = ' '

    def __init__(self, string):
        self.root = self.build_tree(string)

    def build_tree(self, string):
        stack = []
        for s in string.split(self.separator):
            n = Node(s)
            if s == OP.NOT:
                op1 = stack.pop()
                n.r = op1
            if (s == OP.IMPLIES) or (s == OP.AND) or (s == OP.OR):
                op1 = stack.pop()
                op2 = stack.pop()
                n.r = op1
                n.l = op2
            stack.append(n)
        return stack.pop()

    def show(self):
        self.root.print_tree(0)

def nnf(node):
    """Converts a formula into Negation Normal Form

    Arguments:
    node: The root node of the formula tree
    Returns:
    The root node of the formula in NNF
    """

    newnode = node
    if node.val == OP.NOT:
        if node.r.is_literal():
            if node.r.val == LIT.TRUE:
                newnode = Node(LIT.FALSE)
            elif node.r.val == LIT.FALSE:
                newnode = Node(LIT.TRUE)
            return newnode
        else:
            if node.r.val == OP.NOT:
                if node.r.r.val == OP.NOT:
                    newnode = node.r.r
                else:
                    newnode.r = nnf(node.r)
                    return newnode
            elif node.r.val == OP.AND:
                newnode = Node(OP.OR)
                newnode.l = Node(OP.NOT)
                newnode.l.r = node.r.l
                newnode.r = Node(OP.NOT)
                newnode.r.r = node.r.r
            elif node.r.val == OP.OR:
                newnode = Node(OP.AND)
                newnode.l = Node(OP.NOT)
                newnode.l.r = node.r.l
                newnode.r = Node(OP.NOT)
                newnode.r.r = node.r.r
            elif node.r.val == OP.IMPLIES:
                newnode = Node(OP.AND)
                newnode.l = Node(OP.NOT)
                newnode.l.r = Node(OP.NOT)
                newnode.l.r.r = node.r.l
                newnode.r = Node(OP.NOT)
                newnode.r.r = node.r.r
    if not newnode.is_literal():
        if newnode.val == OP.NOT:
            newnode = nnf(newnode)
        else:
            newnode.l = nnf(newnode.l)
            newnode.r = nnf(newnode.r)
    return newnode

def tautology(f):
    """Checks if a formula f is a tautology"""
    for x in f[0]:
        if x in f[2]:
            return True
    return False

def subsumed(f, l):
    """Checks if a formula f is subsumed in a list of formulas l"""
    for g in l:
        satisfies = True
        for a in g[0]:
            if a in f[0]:
                pass
            else:
                satisfies = False
        for b in g[2]:
            if b in f[2]:
                pass
            else:
                satisfies = False
        if satisfies:
            return True
    return False

def to_asp(f):
    """Transforms a normalized string formula into ASP syntax"""
    f = f.replace('-', 'not ')
    f = f.replace(LIT.TRUE, '#true')
    f = f.replace(LIT.FALSE, '#false')
    l = f.split(' > ', 1)
    head = l[1].split(' | ')
    body = l[0].split(' & ')
    asp_form = ''
    if (len(body) == 1) and (body[0] == ''):
        asp_form = ', '.join(head)
    else:
        asp_form = ', '.join(head) + ' :- ' + ', '.join(body)
    return asp_form + '.'

def normalization(node, simplify=True):
    """Wrapper function for normalize()

    Arguments:
    node: The root node of the formula in NNF
    Returns:
    A set of normalized string formulas
    """

    t = None
    solution = set([])
    if node.val == OP.IMPLIES:
        t = ([], [node.l], [], [node.r])
    else:
        t = ([], [], [], [node])
    normlist = normalize([], [t])
    no_taut_list = [g for g in normlist if not tautology(g)]
    no_subs_list = [g for g in no_taut_list
                    if not subsumed(g, difference(list(normlist), [g]))]
    for g in normlist:
        s = ''
        l = [x.get_string() for x in g[0]]
        s += ' & '.join(l)
        s += ' > '
        r = [x.get_string() for x in g[2]]
        s += ' | '.join(r)
        solution.add(s)
    return solution

def normalize(st, sn):
    """Normalize a set of propositional formulas to the form: p & q -> r | s

    Arguments:
    st: List of normalized formulas
    sn: List of propositional formulas to normalize
    Returns:
    A list or normalized formulas. Antecedent literals are in f[0], consequent
    literals are in f[2]
    Data Types:
    The formulas in st and sn must be a 4-tuple of lists, each of them containing
    one or more Node objects:
    f[0]: finished antecedent literals
    f[1]: unfinished antecedent formulas
    f[2]: finished consequent literals
    f[3]: unfinished consequent formulas
    Additional notes:
    During execution, the algorithm checks that the above lists do not contain
    duplicate elements (behaving like a set). The reason not to use a set-based
    implementation is that Node elements are mutable, and therefore not
    hashable (required by frozenset).
    """

    # ITERATIVE VERSION
    while len(sn) <> 0:
        f = sn.pop()
        newformulas = []
        if len(f[3]) <> 0:
            newformulas.extend(apply_substitution(f, 'right'))
        elif len(f[1]) <> 0:
            newformulas.extend(apply_substitution(f, 'left'))
        else:
            newformulas.append(f)

        if newformulas == [f]:
            st.extend(newformulas)
        else:
            sn.extend(newformulas)
    return st

    # RECURSIVE VERSION
    # # Base case
    # if len(sn) == 0:
    #     return st

    # # General case
    # # print st, sn
    # f = sn.pop()
    # newformulas = []
    # if len(f[3]) <> 0:
    #     newformulas.extend(apply_substitution(f, 'right'))
    # elif len(f[1]) <> 0:
    #     newformulas.extend(apply_substitution(f, 'left'))
    # else:
    #     newformulas.append(f)

    # if newformulas == [f]:
    #     newst = list(st)
    #     newst.extend(newformulas)
    #     return normalize(newst, sn)
    # else:
    #     newsn = list(sn)
    #     newsn.extend(newformulas)
    #     return normalize(st, newsn)

def apply_substitution(f, side):
    """Search for an applicable substitution rule and apply it.

    Arguments:
    f: The formula to operate with
    side: 'left' or 'right'
    Returns:
    A list with the new rules.
    """

    substitution_rules = {
        'left': [L1, L2, L3, L4, L5, L6, L7],
        'right': [R1, R2, R3, R4, R5, R6, R7]
        }
    for rule in substitution_rules[side]:
        applicable, result = rule(f)
        if applicable:
            for i in result:
                for j in i:
                    for h in j:
                        print h.get_string()
            return result
    return []

def union(l, s):
    for x in s:
        if x not in l:
            l.append(x)
    return l

def difference(l, s):
    for x in s:
        try:
            l.remove(x)
        except ValueError:
            pass
    return l

def L1(f):
    for a in f[1]:
        if a.val == LIT.FALSE:
            print 'L1'
            return True, []
    return False, []

def L2(f):
    for a in f[1]:
        if a.val == LIT.TRUE:
            print 'L2'
            g = (list(f[0]),
                 difference(list(f[1]), [a]),
                 list(f[2]),
                 list(f[3]))
            return True, [g]
    return False, []

def L3(f):
    for a in f[1]:
        if a.is_literal() or ((a.val == OP.NOT) and a.r.is_literal()):
            print 'L3'
            g = (union(list(f[0]), [a]),
                 difference(list(f[1]), [a]),
                 list(f[2]),
                 list(f[3]))
            return True, [g]
    return False, []

def L4(f):
    for a in f[1]:
        if (a.val == OP.NOT) and (a.r.val == OP.NOT):
            print 'L4'
            g = (list(f[0]),
                 difference(list(f[1]), [a]),
                 list(f[2]),
                 union(list(f[3]), [a.r]))
            return True, [g]
    return False, []

def L5(f):
    for a in f[1]:
        if a.val == OP.AND:
            print 'L5'
            g = (list(f[0]),
                 union(difference(list(f[1]), [a]), [a.l, a.r]),
                 list(f[2]),
                 list(f[3]))
            return True, [g]
    return False, []

def L6(f):
    for a in f[1]:
        if a.val == OP.OR:
            print 'L6'
            g = (list(f[0]),
                 union(difference(list(f[1]), [a]), [a.l]),
                 list(f[2]),
                 list(f[3]))
            h = (list(f[0]),
                 union(difference(list(f[1]), [a]), [a.r]),
                 list(f[2]),
                 list(f[3]))
            return True, [g, h]
    return False, []

def L7(f):
    for a in f[1]:
        if a.val == OP.IMPLIES:
            print 'L7'

            x = nnf(Node(OP.NOT, right=a.l))
            g = (list(f[0]),
                 union(difference(list(f[1]), [a]), [x]),
                 list(f[2]),
                 list(f[3]))

            h = (list(f[0]),
                 union(difference(list(f[1]), [a]), [a.r]),
                 list(f[2]),
                 list(f[3]))

            z = nnf(Node(OP.NOT, right=a.r))
            i = (list(f[0]),
                 difference(list(f[1]), [a]),
                 list(f[2]),
                 union(list(f[3]), [a.l, z]))
            return True, [g, h, i]
    return False, []

def R1(f):
    for b in f[3]:
        if b.val == LIT.TRUE:
            print 'R1'
            return True, []
    return False, []

def R2(f):
    for b in f[3]:
        if b.val == LIT.FALSE:
            print 'R2'
            g = (list(f[0]),
                 list(f[1]),
                 list(f[2]),
                 difference(list(f[3]), [b]))
            return True, [g]
    return False, []

def R3(f):
    for b in f[3]:
        if b.is_literal() or ((b.val == OP.NOT) and b.r.is_literal()):
            print 'R3'
            g = (list(f[0]),
                 list(f[1]),
                 union(list(f[2]), [b]),
                 difference(list(f[3]), [b]))
            return True, [g]
    return False, []

def R4(f):
    for b in f[3]:
        if (b.val == OP.NOT) and (b.r.val == OP.NOT):
            print 'R4'
            g = (list(f[0]),
                 union(list(f[1]), [b.r]),
                 list(f[2]),
                 difference(list(f[3]), [b]))
            return True, [g]
    return False, []

def R5(f):
    for b in f[3]:
        if b.val == OP.OR:
            print 'R5'
            g = (list(f[0]),
                 list(f[1]),
                 list(f[2]),
                 union(difference(list(f[3]), [b]), [b.l, b.r]))
            return True, [g]
    return False, []

def R6(f):
    for b in f[3]:
        if b.val == OP.AND:
            print 'R6'
            g = (list(f[0]),
                 list(f[1]),
                 list(f[2]),
                 union(difference(list(f[3]), [b]), [b.l]))
            h = (list(f[0]),
                 list(f[1]),
                 list(f[2]),
                 union(difference(list(f[3]), [b]), [b.r]))
            return True, [g, h]
    return False, []

def R7(f):
    for b in f[3]:
        if b.val == OP.IMPLIES:
            print 'R7'
            g = (list(f[0]),
                 union(list(f[1]), [b.l]),
                 list(f[2]),
                 union(difference(list(f[3]), [b]), [b.r]))

            v = nnf(Node(OP.NOT, right=b.r))
            w = nnf(Node(OP.NOT, right=b.l))
            h = (list(f[0]),
                 union(list(f[1]), [v]),
                 list(f[2]),
                 union(difference(list(f[3]), [b]), [w]))
            return True, [g, h]
    return False, []


class NormTest(unittest.TestCase):

    f1 = Formula('s r | - q p - - & - >')
    f2 = Formula('s r | q | p | - q p - - & - >')
    f3 = Formula('s /f - - | - q /t - - & - >')

    l2l4l5 = Formula('/t q - - & p >')    # /t & --q > p
    l7     = Formula('q - - p > r >')     # (--q > p) > r
    r2r4r5 = Formula('q p - - /f | >')    # q > --p | /f
    r7     = Formula('r q p > >')         # r > (q > p)
    l7r7   = Formula('q p > s r > >')     # (q > p) > (s > r)
    l7l6   = Formula('p q > r s > | t >')  # (p > q) | (r > s) > t
    r7r6   = Formula('t p q > r s > & >')  # t > (p > q) & (r > s)
    l6r6   = Formula('q p | s r & >')     # q | p > s & r
    l1r1   = Formula('/t p & q /f | >')   # /t | p > q & /f

    simple = Formula('q p |')
    example = Formula('p - q > p r > - >')
    constraint = Formula('noche noche dia & /f > &')

    def test_nnf(self):
        self.assertEqual(nnf(self.f1.root).get_string(), '-s&-r>-q|-p')
        self.assertEqual(nnf(self.f2.root).get_string(), '-s&-r&-q&-p>-q|-p')
        self.assertEqual(nnf(self.f3.root).get_string(), '-s&/t>-q|/f')

    def test_l2l4l5(self):
        f = nnf(self.l2l4l5.root)
        s = {' > p | -q'}
        self.assertEqual(normalization(f), s)

    def test_l7(self):
        f = nnf(self.l7.root)
        s = {'-q > r',
             'p > r',
             '-q > r | -p'}
        self.assertEqual(normalization(f), s)

    def test_r2r4r5(self):
        f = nnf(self.r2r4r5.root)
        s = {'q & -p > '}
        self.assertEqual(normalization(f), s)

    def test_r7(self):
        f = nnf(self.r7.root)
        s = {'r & q > p',
             'r & -p > -q'}
        self.assertEqual(normalization(f), s)

    def test_l7r7(self):
        f = nnf(self.l7r7.root)
        s = {'s & p > r',
             's & -q > r',
             's > r | q | -p',
             '-r & p > -s',
             '-r > -s | q | -p',
             '-r & -q > -s'}
        self.assertEqual(normalization(f), s)

    def test_l7l6(self):
        f = nnf(self.l7l6.root)
        s = {'-p > t',
             'q > t',
             ' > t | p | -q',
             '-r > t',
             's > t',
             ' > t | r | -s'}
        self.assertEqual(normalization(f), s)

    def test_r7r6(self):
        f = nnf(self.r7r6.root)
        s = {'t & p > q',
             't & -q > -p',
             't & r > s',
             't & -s > -r'}
        self.assertEqual(normalization(f), s)

    def test_l6r6(self):
        f = nnf(self.l6r6.root)
        s = {'q > s',
             'q > r',
             'p > s',
             'p > r'}
        self.assertEqual(normalization(f), s)

    def test_l1r1(self):
        f = nnf(self.l1r1.root)
        s = {'p > q'}
        self.assertEqual(normalization(f), s)

    def test_simple(self):
        f = nnf(self.simple.root)
        s = {' > q | p'}
        self.assertEqual(normalization(f), s)

    def test_paper_example(self):
        f = nnf(self.example.root)
        s = {' > -r | -p',
             'q > -r',
             '-p > -p | -q',
             '-p > -p',
             ' > -r | -p | -q',
             '-p & q > '}
        self.assertEqual(normalization(f), s)

if __name__ == '__main__':

    #TODO: adapt for subsumed+taut checking
    #unittest.main()

    f = NormTest.constraint
    f.show()
    g = nnf(f.root)
    print '----'
    g.print_tree(0)

    for i in normalization(g):
        print i
        print to_asp(i)
