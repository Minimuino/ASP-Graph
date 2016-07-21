# -*- coding: utf-8 -*-

"""NORMALIZATION MODULE
Transforms HT propositional formulas into logic programs with the form:
p1 & p2 & ... & pN -> q1 | q2 | ... | qM
"""

import string

f1 = 's r | - q p - - - & - >'
f2 = 's r | q | p | - q p - - & - >'
f3 = 's /f - - | - q /t - - & - >'

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

    def is_literal(self):
        if ((self.val == OP.NOT) or (self.val == OP.IMPLIES)
            or (self.val == OP.AND) or (self.val == OP.OR)):
            return False
        else:
            return True

    def print_tree(self, n):
        if self.l:
            self.l.print_tree(n+1)
        print ' '*2*n, self.val
        if self.r:
            self.r.print_tree(n+1)

    def get_string(self):
        string = ''
        if self.r:
            string += self.r.get_string()
        string += self.val
        if self.l:
            string += self.l.get_string()
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
                n.l = op1
            if (s == OP.IMPLIES) or (s == OP.AND) or (s == OP.OR):
                op1 = stack.pop()
                op2 = stack.pop()
                n.l = op1
                n.r = op2
            stack.append(n)
        return stack.pop()

    def show(self):
        self.root.print_tree(0)

def nnf(node):
    """Converts a formula into Negation Normal Form

    Arguments:
    node: The root node of the formula tree
    Returns:
    """

    newnode = node
    if node.val == OP.NOT:
        if node.l.is_literal():
            if node.l.val == LIT.TRUE:
                newnode = Node(LIT.FALSE)
            elif node.l.val == LIT.FALSE:
                newnode = Node(LIT.TRUE)
            return newnode
        else:
            if node.l.val == OP.NOT:
                newnode = node.l.l
            elif node.l.val == OP.AND:
                newnode = Node(OP.OR)
                newnode.l = Node(OP.NOT)
                newnode.l.l = node.l.l
                newnode.r = Node(OP.NOT)
                newnode.r.l = node.l.r
            elif node.l.val == OP.OR:
                newnode = Node(OP.AND)
                newnode.l = Node(OP.NOT)
                newnode.l.l = node.l.l
                newnode.r = Node(OP.NOT)
                newnode.r.l = node.l.r
            elif node.l.val == OP.IMPLIES:
                newnode = Node(OP.AND)
                newnode.l = node.l.l
                newnode.r = Node(OP.NOT)
                newnode.r.l = node.l.r
    if not newnode.is_literal():
        if newnode.val == OP.NOT:
            newnode = nnf(newnode)
        else:
            newnode.l = nnf(newnode.l)
            newnode.r = nnf(newnode.r)
    return newnode

def normalize(st, sn):
    """Normalize a set of propositional formulas to the form: p & q -> r | s

    Arguments:
    st: Set of normalized formulas
    sn: Set of propositional formulas to normalize
    Data Types:
    The formulas in st and sn must be a 4-tuple of sets, each of them containing
    one or more Node objects:
    f[0]: finished antecedent literals
    f[1]: unfinished antecedent formulas
    f[2]: finished consecuent literals
    f[3]: unfinished consecuent formulas
    Returns:
    """

    # Base case
    if len(sn) == 0:
        return st

    # General case
    # print st, sn
    f = sn.pop()
    newformulas = set([])
    if len(f[3]) <> 0:
        newformulas.update(apply_substitution(f, 'right'))
    elif len(f[1]) <> 0:
        newformulas.update(apply_substitution(f, 'left'))
    else:
        newformulas.add(f)

    if newformulas == {f}:
        return normalize(st.union(newformulas), sn)
    else:
        return normalize(st, sn.union(newformulas))

def apply_substitution(f, side):
    """Search for an applicable substitution rule and apply it.

    Arguments:
    f: The formula to operate with
    side: 'left' or 'right'
    Returns:
    A set with the new rules.
    """

    substitution_rules = {
        'left': [L1, L2, L3, L4, L5, L6, L7],
        'right': [R1, R2, R3, R4, R5, R6, R7]
        }
    for rule in substitution_rules[side]:
        applicable, result = rule(f)
        if applicable:
            return result
    return set([])

def L1(f):
    for a in f[1]:
        if a.val == LIT.FALSE:
            return True, set([])
    return False, set([])

def L2(f):
    for a in f[1]:
        if a.val == LIT.TRUE:
            g = (f[0].copy(),
                 f[1].difference({a}),
                 f[2].copy(),
                 f[3].copy())
            return True, {g}
    return False, set([])

def L3(f):
    for a in f[1]:
        if a.is_literal() or ((a.val == OP.NOT) and a.l.is_literal()):
            g = (f[0].union({a}),
                 f[1].difference({a}),
                 f[2].copy(),
                 f[3].copy())
            return True, {g}
    return False, set([])

def L4(f):
    for a in f[1]:
        if (a.val == OP.NOT) and (a.l.val == OP.NOT):
            g = (f[0].copy(),
                 f[1].difference({a}),
                 f[2].copy(),
                 f[3].union({a.l}))
            return True, {g}
    return False, set([])

def L5(f):
    for a in f[1]:
        if a.val == OP.AND:
            g = (f[0].copy(),
                 f[1].difference({a}).union({a.l, a.r}),
                 f[2].copy(),
                 f[3].copy())
            return True, {g}
    return False, set([])

def L6(f):
    for a in f[1]:
        if a.val == OP.OR:
            g = (f[0].copy(),
                 f[1].difference({a}).union({a.l}),
                 f[2].copy(),
                 f[3].copy())
            h = (f[0].copy(),
                 f[1].difference({a}).union({a.r}),
                 f[2].copy(),
                 f[3].copy())
            return True, {g, h}
    return False, set([])

def L7(f):
    for a in f[1]:
        if a.val == OP.IMPLIES:
            g = (f[0].copy(),
                 f[1].difference({a}).union({nnf(Node(OP.NOT, left=a.l))}),
                 f[2].copy(),
                 f[3].copy())
            h = (f[0].copy(),
                 f[1].difference({a}).union({a.r}),
                 f[2].copy(),
                 f[3].copy())
            i = (f[0].copy(),
                 f[1].difference({a}),
                 f[2].copy(),
                 f[3].union({a.l, nnf(Node(OP.NOT, left=a.r))}))
            return True, {g, h, i}
    return False, set([])

def R1(f):
    for b in f[3]:
        if b.val == LIT.TRUE:
            return True, set([])
    return False, set([])

def R2(f):
    for b in f[3]:
        if b.val == LIT.FALSE:
            g = (f[0].copy(),
                 f[1].copy(),
                 f[2].copy(),
                 f[3].difference({b}))
            return True, {g}
    return False, set([])

def R3(f):
    for b in f[3]:
        if b.is_literal() or ((b.val == OP.NOT) and b.l.is_literal()):
            g = (f[0].copy(),
                 f[1].copy(),
                 f[2].union({b}),
                 f[3].difference({b}))
            return True, {g}
    return False, set([])

def R4(f):
    for b in f[3]:
        if (b.val == OP.NOT) and (b.l.val == OP.NOT):
            g = (f[0].copy(),
                 f[1].union({b.l}),
                 f[2].copy(),
                 f[3].difference({b}))
            return True, {g}
    return False, set([])

def R5(f):
    for b in f[3]:
        if b.val == OP.OR:
            g = (f[0].copy(),
                 f[1].copy(),
                 f[2].copy(),
                 f[3].difference({b}).union({b.l, b.r}))
            return True, {g}
    return False, set([])

def R6(f):
    for b in f[3]:
        if b.val == OP.AND:
            g = (f[0].copy(),
                 f[1].copy(),
                 f[2].copy(),
                 f[3].difference({b}).union({b.l}))
            h = (f[0].copy(),
                 f[1].copy(),
                 f[2].copy(),
                 f[3].difference({b}).union({b.r}))
            return True, {g, h}
    return False, set([])

def R7(f):
    for b in f[3]:
        if b.val == OP.IMPLIES:
            g = (f[0].copy(),
                 f[1].union({b.l}),
                 f[2].copy(),
                 f[3].difference({b}).union({b.r}))
            h = (f[0].copy(),
                 f[1].union({nnf(Node(OP.NOT, left=b.r))}),
                 f[2].copy(),
                 f[3].difference({b}).union({nnf(Node(OP.NOT, left=b.l))}))
            return True, {g, h}
    return False, set([])

if __name__ == '__main__':

    f = Formula(f1)
    f.show()
    g = nnf(f.root)
    print '----'
    g.print_tree(0)

    t = (frozenset([]), frozenset([g.l]), frozenset([]), frozenset([g.r]))
    for f in normalize(set([]), {t}):
        s = ''
        l = [x.get_string() for x in f[0]]
        s += ' & '.join(l)
        s += ' > '
        l = [x.get_string() for x in f[2]]
        s += ' | '.join(l)
        print s
