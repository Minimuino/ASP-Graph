# -*- coding: utf-8 -*-

import string

'''
NORMALIZATION MODULE
   Transforms HT logic formulas into logic programs.
   Assumes HT formulas are in negation normal form (NNF).
'''

f1 = 's r | - q p - - & - >'
f2 = 's r | q | p | - q p - - & - >'

# Enum class for opcodes
class OP:
    NOT = '-'
    IMPLIES = '>'
    AND = '&'
    OR = '|'

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
    newnode = node
    if node.val == OP.NOT:
        if node.l.is_literal():
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

if __name__ == '__main__':
    f = Formula(f1)
    f.show()
    g = nnf(f.root)
    print '----'
    g.print_tree(0)
