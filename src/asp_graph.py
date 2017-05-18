# -*- coding: utf-8 -*-

import os
import string

import kivy.core.window as window
import kivy.graphics as graphics
import kivy.lang as lang
import kivy.properties as prop
import kivy.uix.widget as widget
import kivy.uix.label as label
import kivy.animation as anim

from normalization import LIT

# Enum class for drawing modes
class Mode:
    INSERT, SELECT, RESIZE = range(3)

# Enum class for adding objects
class Item:
    ATOM, ELLIPSE, SQUARE, LINE = range(4)

class Transform:
    size_t = [1, 1]

class GenericWidget(widget.Widget):

    default_color = [.941, .941, .941]
    shadowed_color = [.800, .800, .800]

    def __init__(self, parent_color=[.0, .0, .0], **kwargs):
        self.resize_factor = [1, 1, 0, 0]
        color = self.default_color
        # print self, parent_color, self.default_color
        if parent_color == self.default_color:
            color = self.shadowed_color
        super(GenericWidget, self).__init__(color=color, **kwargs)

    # def on_parent(self, instance, value):
    #     # print self, parent_color, self.default_color
    #     if not isinstance(self, RootWidget):
    #         if self.parent.color == self.default_color:
    #             self.color = self.shadowed_color

    # def get_color(self):
    #     color = (0., 0., 0.)
    #     if (self.iden % 2) <> 0:
    #         color = (.800, .800, .800)
    #     else:
    #         color = (.941, .941, .941)
    #     return color

    def contained(self, widget):
        # Returns True if self is contained in widget. False otherwise
        if isinstance(widget, EllipseWidget):
            if (widget.collide_point(self.x, self.y) and
                widget.collide_point(self.x, self.top) and
                widget.collide_point(self.right, self.y) and
                widget.collide_point(self.right, self.top)):
                return True
            else:
                return False
        else:
            if (self.x > widget.x and
                self.y > widget.y and
                self.right < widget.right and
                self.top < widget.top):
                return True
            else:
                return False

    def collide_widget(self, widget):
        if isinstance(widget, EllipseWidget):
            if (widget.collide_point(self.x, self.y) or
                widget.collide_point(self.x, self.top) or
                widget.collide_point(self.right, self.y) or
                widget.collide_point(self.right, self.top)):
                return True
            points = None
            i = 0
            for ch in widget.canvas.children:
                if isinstance(ch, graphics.vertex_instructions.Line):
                    points = ch.points
            while i < (len(points)-1):
                px = points[i]
                py = points[i+1]
                i += 2
                if self.collide_point(px, py):
                    return True
            return False
        else:
            return super(GenericWidget, self).collide_widget(widget)

    def translate(self, factor):
        self.pos = [self.x + factor[0], self.y + factor[1]]

    def scale(self, factor, origin):
        self.size = [self.size[0] * factor, self.size[1] * factor]
        self.pos = [origin[0] + (self.x-origin[0]) * factor,
                    origin[1] + (self.y-origin[1]) * factor]
        # self.anim = anim.Animation(size=newsize, d=.1, t='linear').start(self)
        # self.anim = anim.Animation(pos=newpos, d=.1, t='linear').start(self)

    def check_constraints(self):
        if not self.contained(self.parent):
            return False
        for brother in self.parent.children:
            if (brother is not self) and (self.collide_widget(brother)):
                return False
        if (not isinstance(self, AtomWidget) and
            Line.test_all_collisions(self)):
            return False
        return True

    def move(self, dx, dy, do_check=True):
        # Update pos
        oldx = self.x
        oldy = self.y
        self.x = self.x + dx
        # Move constraints
        if do_check and not self.check_constraints():
            self.x = oldx
            dx = 0
        self.y = self.y + dy
        if do_check and not self.check_constraints():
            self.y = oldy
            dy = 0
        # Propagate move through children
        if (dx != 0) or (dy != 0):
            for ch in self.children:
                if isinstance(ch, GenericWidget):
                    ch.move(dx, dy, do_check=False)

    def resize(self, dx, dy, touch):
        # Update size
        oldsize = [self.size[0], self.size[1]]
        oldpos = [self.x, self.y]
        rfx = self.resize_factor[0]
        rfy = self.resize_factor[1]
        rpx = self.resize_factor[2]
        rpy = self.resize_factor[3]
        self.size = (self.size[0] + rfx*dx, self.size[1] + rfy*dy)
        if touch.ud['add']:
            self.x += dx*rpx
            self.y += dy*rpy
            if touch.x < self.x:
                self.resize_factor[0] = -1
                self.resize_factor[2] = 1
            elif touch.x > self.right:
                self.resize_factor[0] = 1
                self.resize_factor[2] = 0
            if touch.y < self.y:
                self.resize_factor[1] = -1
                self.resize_factor[3] = 1
            elif touch.y > self.top:
                self.resize_factor[1] = 1
                self.resize_factor[3] = 0
        # Size constraints
        if (self.size[0] < 1 or self.size[1] < 1):
            self.size = oldsize
            self.pos = oldpos
            return
        if not self.check_constraints():
            self.size = oldsize
            self.pos = oldpos
            return
        for ch in self.children:
            if isinstance(ch, GenericWidget):
                if not ch.contained(self):
                    self.size = oldsize
                    self.pos = oldpos
                    return

    def add(self, touch, item):
        if item == Item.ATOM:
            if AtomWidget.active_atom == None:
                return None
            w = AtomWidget(parent_color=self.color, pos=touch.pos)
            # Need to update label texture in order to get its actual size
            w.ids.customlabel.texture_update()
            # Init position correction
            w.pos = (w.pos[0] - w.width/2, w.pos[1] - w.height/2)
            #print w.size
        elif item == Item.ELLIPSE:
            w = EllipseWidget(default_children=False,
                              parent_color=self.color,
                              pos=(touch.x, touch.y))
        elif item == Item.SQUARE:
            if not isinstance(self, EllipseWidget):
                return None
            w = SquareWidget(default_children=False,
                             parent_color=self.color,
                             pos=touch.pos)
        elif item == Item.LINE:
            w = NexusWidget(pos=touch.pos)

        self.add_widget(w)
        if isinstance(w, NexusWidget):
            w.attach_line()
            return w

        # Check creation constraints
        if not w.check_constraints():
            w.delete()
            return None

        touch.grab(w, exclusive=True)
        touch.ud['ppos'] = (touch.x, touch.y)
        touch.ud['mode'] = Mode.RESIZE
        touch.ud['add'] = True
        return w

    def delete(self):
        for ch in self.children:
            ch.delete()
        self.parent.remove_widget(self)

    def on_touch_down(self, touch, mode=Mode.SELECT, item=Item.ATOM):

        for child in self.children[:]:
            if child.dispatch('on_touch_down', touch, mode, item):
                return True

        if self.collide_point(*touch.pos) == False:
            return False

        print self, mode
        #print self.size
        if mode ==  Mode.INSERT:
            if 'button' in touch.profile:
                # ADD
                if touch.button == 'left':
                    self.add(touch, item)
                # DELETE
                elif touch.button == 'right':
                    self.delete()
                    #print 'Deleting ', self, ' from ', self.parent
        elif mode == Mode.SELECT:
            if 'button' in touch.profile:
                # MOVE
                if touch.button == 'left':
                    touch.grab(self, exclusive=True)
                    touch.ud['offset'] = (self.x-touch.x, self.y-touch.y)
                    touch.ud['mode'] = Mode.SELECT
                # RESIZE
                elif touch.button == 'right':
                    touch.grab(self, exclusive=True)
                    touch.ud['mode'] = Mode.RESIZE
                    touch.ud['add'] = False
                touch.ud['ppos'] = (touch.x, touch.y)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if touch.ud['mode'] == Mode.SELECT:
                dx = touch.x + touch.ud['offset'][0] - self.x
                dy = touch.y + touch.ud['offset'][1] - self.y
                self.move(dx, dy)
            if touch.ud['mode'] == Mode.RESIZE:
                dx = touch.x - touch.ud['ppos'][0]
                dy = touch.y - touch.ud['ppos'][1]
                touch.ud['ppos'] = (touch.x, touch.y)
                self.resize(dx, dy, touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            try:
                if touch.ud['add']:
                    self.resize_factor[0] = 1
                    self.resize_factor[1] = 1
            except KeyError:
                pass

    def show_tree(self, depth):
        if isinstance(self, AtomWidget):
            return 0
        else:
            for ch in self.children:
                print ' '*2*depth, ch
                ch.show_tree(depth+1)
            return 0

    def delete_tree(self):
        for ch in self.children:
            ch.delete_tree()
        self.clear_widgets()

    def get_tree(self, depth):
        strl = []
        strl.append(' '*4*depth + '{0}:'.format(type(self).__name__))
        strl.append(' '*4*(depth+1) + 'pos: {0}'.format(self.pos))
        strl.append(' '*4*(depth+1) + 'size: {0}'.format(self.size))
        if (depth % 2) <> 0:
            strl.append(' '*4*(depth+1) + 'color: .800, .800, .800')
        if isinstance(self, AtomWidget):
            strl.append(' '*4*(depth+1) +
                        'text: \'{0}\''.format(self.text))
        else:
            for ch in self.children:
                strl.append(ch.get_tree(depth+1))
        return string.join(strl, '\n')

    def get_propositional_formula(self):
        if isinstance(self, AtomWidget):
            return self.text
        if isinstance(self, EllipseWidget):
            conjunction = []
            disjuntion = []
            for ch in self.children:
                if isinstance(ch, SquareWidget):
                    disjuntion.append(ch.get_propositional_formula())
                else:
                    conjunction.append(ch.get_propositional_formula())
            if conjunction == []:
                conjunction.append('True')
            if disjuntion == []:
                disjuntion.append('False')
            return '(' + '('+string.join(conjunction, ' AND ')+')' + \
                ' IMPLIES ' + '('+string.join(disjuntion, ' OR ')+')' + ')'
        else:
            strs = []
            for ch in self.children:
                strs.append(ch.get_propositional_formula())
            if strs == []:
                strs.append('True')
            return '(' + string.join(strs, ' AND ') + ')'

    def get_quantifiers_and_equalities(self):
        variables = set()
        quantified_vars = set()
        equalities = set()
        for ch in self.children:
            if isinstance(ch, NexusWidget):
                varlist = ch.get_variables()
                variables.update(set(varlist))
                if len(varlist) > 1:
                    first_var = varlist[0]
                    equalities = {(first_var, v) for v in varlist[1:]}
            elif isinstance(ch, AtomWidget):
                for h in ch.get_active_hooks():
                    variables.update(set(h.get_variables()))
        quantified_vars = variables
        return (quantified_vars, equalities)

    def get_first_order_formula(self, quantified_vars=set()):

        if isinstance(self, AtomWidget):
            return self.get_as_text()

        new_quants, new_eqs = self.get_quantifiers_and_equalities()
        new_quants = new_quants.difference(quantified_vars)
        qlist = ['Exists '+v for v in new_quants]
        eqlist = [eq[0] + ' = ' + eq[1] for eq in new_eqs]
        quantifiers = string.join(qlist, ', ') + ' '

        if isinstance(self, EllipseWidget):
            conjunction = eqlist
            disjuntion = []
            for ch in self.children:
                if isinstance(ch, SquareWidget):
                    subformula = ch.get_first_order_formula(quantified_vars.union(new_quants))
                    disjuntion.append(subformula)
                elif isinstance(ch, NexusWidget):
                    continue
                else:
                    subformula = ch.get_first_order_formula(quantified_vars.union(new_quants))
                    conjunction.append(subformula)
            if conjunction == []:
                conjunction.append('True')
            if disjuntion == []:
                disjuntion.append('False')
            return '('+ quantifiers +'('+string.join(conjunction, ' AND ')+')' \
                + ' IMPLIES ' + '('+string.join(disjuntion, ' OR ')+')' + ')'
        else:
            strs = eqlist
            for ch in self.children:
                if isinstance(ch, NexusWidget):
                    continue
                strs.append(ch.get_first_order_formula(quantified_vars.union(new_quants)))
            if strs == []:
                strs.append('True')
            return '('+ quantifiers + string.join(strs, ' AND ') + ')'

    def get_formula(self):
        return self.get_first_order_formula()

    def get_formula_RPN(self):
        s = ''
        if isinstance(self, AtomWidget):
            s = self.text
        else:
            if isinstance(self, EllipseWidget):
                squares = []
                rest = []
                for ch in self.children:
                    if isinstance(ch, SquareWidget):
                        squares.append(ch.get_formula_RPN())
                    else:
                        rest.append(ch.get_formula_RPN())
                if (len(rest) == 0):
                    s += LIT.TRUE
                if len(rest) > 0:
                    s += rest.pop()
                while rest <> []:
                    s += ' ' + rest.pop() + ' &'
                if (len(squares) == 0):
                    s += ' ' + LIT.FALSE
                if len(squares) > 0:
                    s += ' ' + squares.pop()
                while squares <> []:
                    s += ' ' + squares.pop() + ' |'
                s += ' >'
            else:
                l = []
                for ch in self.children:
                    l.append(ch.get_formula_RPN())
                if len(l) > 0:
                    s += l.pop()
                while l <> []:
                    s += ' ' + l.pop() + ' &'
        return s

class Segment:
    """A Segment is an entity that represents a variable.

    It is formed by 2 points defined by 2 HookWidget of NexusWidget.

    Properties:
      hook0: Reference to the first HookWidget/NexusWidget.
      hook1: Reference to the second HookWidget/NexusWidget.
      render_inst: Reference to the graphics.Line instruction.
      canvas: Canvas to draw render_inst.
    """

    # Reference to RootWidget canvas in order to draw segments on top of
    # everything else
    _canvas = None

    @classmethod
    def set_canvas(cls, canvas):
        cls._canvas = canvas

    @staticmethod
    def side_test(A, B, C):
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

    # Segments AB and CD intersection test
    @classmethod
    def segment_intersection(cls, A, B, C, D):
        return (cls.side_test(A, C, D) != cls.side_test(B, C, D) and
                cls.side_test(A, B, C) != cls.side_test(A, B, D))

    def __init__(self, hook0, hook1):
        self.hook0 = hook0
        self.hook1 = hook1
        self.canvas = Segment._canvas #hook.parent.canvas
        pts = [hook0.center_x, hook0.center_y, hook1.center_x, hook1.center_y]
        with self.canvas:
            self.render_inst = graphics.Line(points=pts, width=2)

    def __contains__(self, hook):
        return (hook is self.hook0) or (hook is self.hook1)

    def update(self):
        pts = [self.hook0.center_x, self.hook0.center_y,
               self.hook1.center_x, self.hook1.center_y]
        with self.canvas:
            self.canvas.remove(self.render_inst)
            self.render_inst = graphics.Line(points=pts, width=2)

    def grab(self, x, y):
        pts = [self.hook0.center_x, self.hook0.center_y, x, y]
        with self.canvas:
            self.canvas.remove(self.render_inst)
            self.render_inst = graphics.Line(points=pts, width=2)

    def attach(self, hook0=None, hook1=None):
        if hook0 is not None:
            self.hook0 = hook0
        if hook1 is not None:
            self.hook1 = hook1
        self.update()

    def delete(self):
        with self.canvas:
            self.canvas.remove(self.render_inst)

    def intersects(self, widget):
        x0, y0 = self.hook0.pos
        x1, y1 = self.hook1.pos
        wx, wy = widget.pos
        wr, wt = widget.right, widget.top
        if ((x0 < wx and x1 < wx) or
            (x0 > wr and x1 > wr) or
            (y0 < wy and y1 < wy) or
            (y0 > wt and y1 > wt)):
            return False
        if (Segment.segment_intersection((x0,y0), (x1,y1), (wx,wy), (wr,wt))
            or
            Segment.segment_intersection((x0,y0), (x1,y1), (wx,wt), (wr,wy))):
            return True
        else:
            return False

class Line:
    """A Line is a list of Segments.

    Properties:
      segment_list: List of Segment.
      hook_list: List of HookWidget.
      grabbed_segment: Reference to the current grabbed segment by the pointer.
      grabbed_hook: Reference to the current grabbed hook by the pointer.
      line_id: Unique ID used for generating the name of a variable in ASP.
    """

    # Global list with a reference to every line
    _lines = []

    @staticmethod
    def set_canvas(canvas):
        Segment.set_canvas(canvas)

    @staticmethod
    def hook_groups(graph):
        result = []
        seen = set()
        def component(node):
            result = set()
            nodes = set([node])
            seen_inner = set()
            while nodes:
                node = nodes.pop()
                seen.add(node)
                seen_inner.add(node)
                nodes |= graph[node] - seen_inner
                result.add(node)
            return result
        for node in graph:
            if node not in seen:
                result.append(component(node))
        # Remove strict subsets
        # TODO: Do this in a more efficient way
        subsets = []
        for g1 in result:
            for g2 in result:
                if g1 < g2:
                    subsets.append(g1)
                    break
        for s in subsets:
            result.remove(s)
        return result

    # TODO: Remove this method if not necessary
    @staticmethod
    def get_container(hook_list):
        h = hook_list[0]
        outermost_parent = h.get_container()
        for h in hook_list:
            parent = h.get_container()
            if parent not in outermost_parent.walk(restrict=True):
                outermost_parent = parent
        return outermost_parent

    @classmethod
    def test_all_collisions(cls, widget):
        for l in cls._lines:
            if (l.intersects(widget)):
                return True
        return False

    @classmethod
    def get_all_lines(cls):
        return tuple(cls._lines)

    def __init__(self, hook):
        self.segment_list = []
        self.hook_list = [hook]
        self.grabbed_segment = None
        self.grabbed_hook = hook
        self.line_id = len(Line._lines)
        self._add_segment(hook, hook)
        Line._lines.append(self)
        # Graph
        self._updated = True
        self._graph = {0: []}
        self._components = [[0]]
        # TODO: remove this attribute if not necessary
        self._containers = [hook.get_container()]

    def _add_segment(self, hook0, hook1):
        s = Segment(hook0, hook1)
        self.segment_list.append(s)
        self.grabbed_segment = s

    # DEPRECATED
    def _get_hooks(self):
        hook_list = [self.segment_list[0].hook0]
        hook_list.extend([s.hook1 for s in self.segment_list])
        return hook_list

    def _get_hook_index(self, hook):
        for i, h in enumerate(self.hook_list):
            if hook is h:
                return i
        return -1

    def _get_connected_hooks(self, hook):
        """Return all Hooks/Nexus connected by one Segment to the given Hook."""
        connected = []
        for s in self.segment_list:
            if hook in s:
                other_hook = s.hook1 if (s.hook0 is hook) else s.hook0
                connected.append(other_hook)
        return connected

    def _get_connected_hooks_lessequal(self, hook):
        """Return all Hooks/Nexus connected by one Segment to the given Hook
        at the same level or lower."""
        connected = []
        for s in self.segment_list:
            if hook in s:
                other_hook = s.hook1 if (s.hook0 is hook) else s.hook0
                if (other_hook.get_container() is hook.get_container() or
                    other_hook.get_container().parent is hook.get_container()):
                    connected.append(other_hook)
        return connected

    def _update_graph(self):
        graph = {}
        for i, hook in enumerate(self.hook_list):
            graph[i] = [self._get_hook_index(h) for h in self._get_connected_hooks_lessequal(hook)]
        self._graph = graph
        set_graph = {key: set(self._graph[key]) for key in self._graph}
        self._components = Line.hook_groups(set_graph)
        hook_groups = [[self.hook_list[i] for i in c] for c in self._components]
        self._containers = [Line.get_container(group) for group in hook_groups]
        self._updated = True

        # def _get_connected_components(self):
        #     #assert self.hook_list == self._get_hooks()
        #     hooks_at_container_level = set([self._get_hook_index(h) for h in self.hook_list
        #                                     if h.get_container() is self._container])
        #     hacl = hooks_at_container_level
        #     graph = self._graph
        #     container_graph = {key: set(graph[key]).intersection(hacl) for key in graph
        #                        if key in hacl}
        #     return Line.connected_components(container_graph)

    def get_segment_ids(self, hook):
        l = []
        for i, s in enumerate(self.segment_list):
            if hook in s:
                l.append(i)
        return l

    def draw_variables(self):
        """Paint every set of segments with a unique color, based on the
        variable of its two hooks.
        """
        if not self._updated:
            self._update_graph()
        for s in self.segment_list:
            vars0 = set(self.get_variables(s.hook0))
            vars1 = set(self.get_variables(s.hook1))
            intersection = vars0.intersection(vars1)
            if intersection:
                var = list(intersection)[0]
                with s.canvas:
                    if var % 2 == 0:
                        graphics.Color(0, 1-0.1*var, 0)
                    elif var % 3 == 0:
                        graphics.Color(0, 0, 1-0.1*var)
                    else:
                        graphics.Color(1-0.1*var, 0, 0)
                    s.update()

    def get_variables(self, hook):
        """Get all variable ids associated to a given hook."""
        if not self._updated:
            self._update_graph()

        varlist = []
        h_index = self._get_hook_index(hook)
        for i, c in enumerate(self._components):
            if h_index in c:
                varlist.append(i)
        return varlist

    def get_all_variables(self):
        return ['x' + str(self.line_id) + '_' + str(var_id)
                for var_id in range(len(self._components))]

    def grab_hook(self, hook):
        self.grabbed_hook = hook
        self._add_segment(hook, hook)

    def grab(self, x, y):
        self.grabbed_segment.grab(x, y)

    def attach_hook(self, hook):
        self.grabbed_segment.attach(hook1=hook)
        self.hook_list.append(hook)
        self._updated = False

    def detach_hook(self, hook):
        # Delete hook
        self.hook_list.remove(hook)
        self._updated = False

        # Delete segments
        segments_to_remove = [s for s in self.segment_list if hook in s]
        for s in segments_to_remove:
            s.delete()
            self.segment_list.remove(s)
            # TODO: Check for connected components, not len(segment_ids)
            other_hook = s.hook1 if (s.hook0 is hook) else s.hook0
            if len(self.get_segment_ids(other_hook)) == 0:
                other_hook.line = None
                if isinstance(other_hook, NexusWidget):
                    other_hook.delete()

        # Check if there is at least one HookWidget attached
        any_predicate = False
        for s in self.segment_list:
            if (not isinstance(s.hook0, NexusWidget) or
                not isinstance(s.hook1, NexusWidget)):
                any_predicate = True
        # If there isn't, delete the whole line
        if not any_predicate:
            self.delete()

    def move_hook(self, hook):
        for s in self.segment_list:
            if hook in s:
                s.update()

    def delete(self):
        for s in self.segment_list:
            s.delete()
            for h in (s.hook0, s.hook1):
                h.line = None
                if isinstance(h, NexusWidget):
                    h.delete()
        self.segment_list = []
        Line._lines.remove(self)

    def intersects(self, widget):
        for s in self.segment_list:
            if s.intersects(widget):
                return True
        return False

class HookWidget(GenericWidget):

    # Reference to the currently grabbed line
    grabbed_line = None

    def __init__(self, **kwargs):
        self.line = None
        super(HookWidget, self).__init__(**kwargs)

    def _toggle_line_item(self):
        # Nasty method for setting current RootWidget item attribute to LINE
        parent = self.parent
        while parent != None:
            if isinstance(parent, RootWidget):
                parent.toggle_line_item()
                break
            else:
                parent = parent.parent

    def resize(self, dx, dy, touch):
        pass

    def translate(self, factor):
        if self.line:
            self.line.move_hook(self)

    def scale(self, factor, origin):
        if self.line:
            self.line.move_hook(self)

    def move(self, dx, dy, do_check=False):
        super(HookWidget, self).move(dx, dy, do_check=do_check)
        if self.line:
            self.line.move_hook(self)

    def add_line(self):
        self.line = Line(self)
        self._toggle_line_item()
        window.Window.bind(mouse_pos=self.on_mouse_pos)
        HookWidget.grabbed_line = self.line

    def delete_line(self):
        if self.line is not None:
            self.line.delete()

    def attach_line(self):
        if self.line is not None:
            return

        # Update line
        self.line = HookWidget.grabbed_line
        self.line.attach_hook(self)

        # Cleanup stuff
        window.Window.unbind(mouse_pos=self.line.grabbed_hook.on_mouse_pos)
        HookWidget.grabbed_line = None
        self._toggle_line_item()

    def detach_line(self):
        if self.line is not None:
            self.line.detach_hook(self)
            self.line = None

    # def on_pos(self, instance, value):
    #     if self.line:
    #         self.line.move_hook(self)

    def on_mouse_pos(self, obj, value):
        self.line.grab(value[0], value[1])

    def on_touch_down(self, touch, mode=Mode.SELECT, item=Item.ATOM):

        if self.disabled:
            return False

        if self.collide_point(*touch.pos) == False:
            return False

        print self, self.line
        if item ==  Item.LINE:
            # ATTACH LINE
            self.attach_line()
        else:
            if 'button' in touch.profile:
                # ADD LINE
                if touch.button == 'left':
                    if self.line is None:
                        self.add_line()
                    else:
                        self.line.draw_variables()
                        print self.line._components
                        print self.line._graph
                # DELETE LINE
                elif touch.button == 'right':
                    self.detach_line()
        return True

    def hide(self):
        self.disabled = True
        self.opacity = 0

    def show(self):
        self.disabled = False
        self.opacity = 1

    def disable(self):
        self.disabled = True
        self.opacity = 0
        if self.line:
            self.line.delete()
            self.line = None

    def get_container(self):
        # Returns the first parent distinct from an AtomWidget
        return self.parent.parent

    def get_line_id(self):
        if self.line:
            return self.line.line_id
        else:
            return None

    def get_all_line_variables(self):
        if self.line:
            return self.line.get_all_variables()
        else:
            return []

    def get_variables(self):
        if self.line:
            return ['x' + str(self.line.line_id) + '_' + str(v)
                    for v in self.line.get_variables(self)]
        else:
            return []

class NexusWidget(HookWidget):

    def __init__(self, **kwargs):
        super(NexusWidget, self).__init__(**kwargs)
        # Init position correction
        self.pos = (self.pos[0] - self.width/2, self.pos[1] - self.height/2)

    def delete(self):
        if self.line is not None:
            self.line.delete()
        if self.parent is not None:
            super(HookWidget, self).delete()

    def translate(self, factor):
        # Do the actual translation
        super(HookWidget, self).translate(factor)
        # Update line position
        super(NexusWidget, self).translate(factor)

    def scale(self, factor, origin):
        # Do the actual scaling (pos only, not size)
        self.pos = [origin[0] + (self.x-origin[0]) * factor,
                    origin[1] + (self.y-origin[1]) * factor]
        # anim.Animation(pos=newpos, d=.1, t='linear').start(self)
        # Update line position
        super(NexusWidget, self).scale(factor, origin)

    def extend_line(self):
        self._toggle_line_item()
        self.line.grab_hook(self)
        window.Window.bind(mouse_pos=self.on_mouse_pos)
        HookWidget.grabbed_line = self.line

    def on_touch_down(self, touch, mode=Mode.SELECT, item=Item.ATOM):

        if self.collide_point(*touch.pos) == False:
            return False

        if item ==  Item.LINE:
            # ATTACH LINE
            self.attach_line()
        else:
            touch.grab(self, exclusive=True)
            touch.ud['offset'] = (self.x-touch.x, self.y-touch.y)
        return True

    def on_touch_move(self, touch):

        if touch.time_update - touch.time_start < 0.2:
            return

        if touch.grab_current is self:
            dx = touch.x + touch.ud['offset'][0] - self.x
            dy = touch.y + touch.ud['offset'][1] - self.y
            # TODO: Check for collisions (except with its own Line)
            self.move(dx, dy, do_check=False)

    def on_touch_up(self, touch):

        if touch.grab_current is self:
            touch.ungrab(self)

        if touch.time_end - touch.time_start > 0.2:
            return

        if 'button' in touch.profile:
            # ADD LINE
            if touch.button == 'left':
                if self.line:
                    self.extend_line()
            # DELETE LINE
            elif touch.button == 'right':
                self.delete()
        return

    def get_container(self):
        return self.parent

    def get_as_text(self, connective='&'):
        txt = ''
        varlist = self.get_variables()
        first_var = varlist[0]
        for i, var in enumerate(varlist[1:], start=1):
            if i > 1:
                txt += ' ' + connective + ' '
            txt += '(' + first_var + ' = ' + var + ')'
        return txt

class Atom(widget.Widget):

    name = prop.StringProperty('')
    hook_points = prop.ObjectProperty([False, False, False, False])

    def __init__(self, name, hook_points, **kwargs):
        # Hook points is a bool list meaning the following:
        # [left, right, top, bottom]
        self.name = name
        self.hook_points = hook_points

class AtomWidget(GenericWidget):

    active_atom = Atom('atom', [False, False, False, False])
    max_scalefactor = 6.2
    show_hooks = True

    def __init__(self, **kwargs):
        super(AtomWidget, self).__init__(**kwargs)
        self.scalefactor = 1

        # self.atom points to an Atom in GlobalContainer.atom_dict
        # The same applies to self.text and self.hook_points
        self.atom = self.active_atom
        self.text = self.atom.name
        self.hook_points = self.atom.hook_points

        # Listen for changes on the Atom at GlobalContainer.atom_dict
        self.atom.bind(hook_points=self.on_hook_points)

        # Internal list to store updated values
        self._hook_points = self.atom.hook_points
        # Init hook points visibility
        self.update()

        # Fade in label
        self.opacity = 0
        anim.Animation(opacity=1, d=.5, t='out_quart').start(self)

    def delete(self):
        self.atom.unbind(hook_points=self.on_hook_points)
        for h in self.get_active_hooks():
            h.detach_line()
        super(AtomWidget, self).delete()

    def resize(self, dx, dy, touch):
        pass

    def scale(self, factor, origin):
        self.scalefactor *= factor
        previous_size = (self.width, self.height)
        super(AtomWidget, self).scale(factor, origin)
        #if self.size[1] >= self.max_height:
        if self.scalefactor >= AtomWidget.max_scalefactor:
            self.size = previous_size

    def update(self):
        if self._hook_points[0]:
            self.ids.hook_left.show()
        else:
            self.ids.hook_left.disable()

        if self._hook_points[1]:
            self.ids.hook_right.show()
        else:
            self.ids.hook_right.disable()

        if self._hook_points[2]:
            self.ids.hook_top.show()
        else:
            self.ids.hook_top.disable()

        if self._hook_points[3]:
            self.ids.hook_bottom.show()
        else:
            self.ids.hook_bottom.disable()

    def on_hook_points(self, instance, value):
        self._hook_points = value
        if AtomWidget.show_hooks:
            self.update()

    def get_active_hooks(self):
        active_hooks = []
        if self._hook_points[0]: active_hooks.append(self.ids.hook_left)
        if self._hook_points[1]: active_hooks.append(self.ids.hook_right)
        if self._hook_points[2]: active_hooks.append(self.ids.hook_top)
        if self._hook_points[3]: active_hooks.append(self.ids.hook_bottom)
        return tuple(active_hooks)

    def get_as_text(self):
        txt = self.text
        has_variables = False
        for h in self.get_active_hooks():
            var = ''
            try:
                var = h.get_variables()[0]
            except IndexError:
                # TODO: Handle this case properly
                # raise EmptyHookError
                pass
            if not has_variables:
                txt += '('
                txt += var
                has_variables = True
            else:
                txt += ', '
                txt += var
        if has_variables:
            txt += ')'
        return txt

class CustomLabel(label.Label):

    def on_texture(self, instance, value):
        print 'texture changed!', instance, value

    def on_touch_down(self, touch, mode=Mode.SELECT, item=Item.ATOM):
        if self.collide_point(*touch.pos) == False:
            return False
        else:
            if mode == Mode.INSERT and touch.button == 'left':
                print self.parent.get_as_text()
                return True
            else:
                return False

    def delete(self):
        pass

    def delete_tree(self):
        self.parent.remove_widget(self)

class SquareWidget(GenericWidget):

    def __init__(self, default_children=False, **kwargs):
        super(SquareWidget, self).__init__(**kwargs)
        # Init position correction
        self.pos = (self.pos[0] - self.size[0]/2, self.pos[1] - self.size[1]/2)
        # Default children
        if default_children:
            at = AtomWidget(parent_color=self.color,
                            pos=(self.x + self.size[0]/2,
                                 self.y + self.size[1]/2))
            self.add_widget(at)

class EllipseWidget(GenericWidget):

    def __init__(self, default_children=False, **kwargs):
        super(EllipseWidget, self).__init__(**kwargs)
        # Init position correction
        self.pos = (self.pos[0] - self.size[0]/2, self.pos[1] - self.size[1]/2)
        # Default children
        if default_children:
            sq = SquareWidget(default_children=True, parent_color=self.color,
                              pos=(self.x + self.size[0]/2,
                                   self.y + self.size[1]/2))
            at = AtomWidget(parent_color=self.color,
                            pos=(self.x + self.size[0]/2,
                                 self.y + self.size[1]/1.2))
            self.add_widget(sq)
            self.add_widget(at)

    def collide_point(self, x, y):
        rx = self.dx/2
        ry = self.dy/2
        v = ((x-self.center[0])/rx)**2 + ((y-self.center[1])/ry)**2
        if v <= 1:
            return True
        else:
            return False

    # def contained_old(self, widget):
    #     points = None
    #     i = 0
    #     for ch in self.canvas.children:
    #         if isinstance(ch, graphics.vertex_instructions.SmoothLine):
    #             points = ch.points
    #     while i < (len(points)-1):
    #         px = points[i]
    #         py = points[i+1]
    #         i += 2
    #         if not widget.collide_point(px, py):
    #             print px, py, self.pos
    #             #print self.previous[i], self.previous[i+1], self.oldpos
    #             return False
    #     self.previous = points
    #     return True

    # def contained(self, widget):
    #     if (widget.collide_point(self.a1[0], self.a1[1]) and
    #         widget.collide_point(self.a2[0], self.a2[1]) and
    #         widget.collide_point(self.b1[0], self.b1[1]) and
    #         widget.collide_point(self.b2[0], self.b2[1])):
    #         return True
    #     else:
    #         return False


class RootWidget(GenericWidget):

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        self.mode = Mode.INSERT
        self.item = Item.ATOM
        self.scale_factor = 1
        self.translate_factor = [1, 1]
        self._prev_item = Item.ATOM

        self.reset_line_canvas()

        # Nasty patch to solve a problem with color when the first widget
        # is added. Simply add and remove a widget in order to let kivy
        # load some stupid object properties.
        w = EllipseWidget(default_children=True,
                          parent_color=(0, 0, 0),#self.color,
                          pos=(0, 0))
        self.add_widget(w)
        self.remove_widget(w)
        #print self.color

    def on_model(self, m):
        print m

    def move(self, dx, dy):
        pass

    def resize(self, dx, dy, touch):
        pass

    def delete(self):
        pass

    def delete_root(self):
        self.parent.remove_widget(self)

    def delete_atom(self, name):
        for w in self.walk(restrict=True):
            if isinstance(w, AtomWidget):
                if w.text == name:
                    w.delete()

    def translate(self, factor):
        pass

    def scale(self, factor, origin):
        pass

    def on_touch_down(self, touch):

        if self.collide_point(*touch.pos) == False:
            return False

        if 'button' in touch.profile:
            if touch.button == 'scrolldown':
                self.scale_factor = 1.1
                for w in self.walk(restrict=True):
                    if isinstance(w, GenericWidget):
                        w.scale(self.scale_factor, touch.pos)
            if touch.button == 'scrollup':
                self.scale_factor = 0.9
                for w in self.walk(restrict=True):
                    if isinstance(w, GenericWidget):
                        w.scale(self.scale_factor, touch.pos)
            if touch.button == 'middle':
                touch.grab(self, exclusive=True)
                touch.ud['ppos'] = (touch.x, touch.y)
        super(RootWidget, self).on_touch_down(touch, self.mode, self.item)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            dx = touch.x - touch.ud['ppos'][0]
            dy = touch.y - touch.ud['ppos'][1]
            touch.ud['ppos'] = (touch.x, touch.y)
            self.translate_factor[0] = dx
            self.translate_factor[1] = dy
            for w in self.walk(restrict=True):
                if isinstance(w, GenericWidget):
                    w.translate(self.translate_factor)

    def toggle_line_item(self):
        if self.item == Item.LINE:
            self.item = self._prev_item
        else:
            self._prev_item = self.item
            self.item = Item.LINE

    def reset_line_canvas(self):
        Line.set_canvas(self.canvas)

    def show_hooks(self):
        AtomWidget.show_hooks = True
        for w in self.walk(restrict=True):
            if isinstance(w, AtomWidget):
                w.update()
            if isinstance(w, NexusWidget):
                w.show()

    def hide_hooks(self):
        AtomWidget.show_hooks = False
        for w in self.walk(restrict=True):
            if isinstance(w, HookWidget):
                w.hide()
