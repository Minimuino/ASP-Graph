# -*- coding: utf-8 -*-

import os
import string

import kivy.core.window as window
import kivy.graphics as graphics
import kivy.lang as lang
import kivy.properties as prop
import kivy.uix.widget as widget
import kivy.uix.label as label

import hover_behavior as hover
from normalization import LIT
import kwad


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
            points = None
            i = 0
            for ch in widget.canvas.children:
                if isinstance(ch, graphics.vertex_instructions.SmoothLine):
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

    def move(self, dx, dy, check_constraints=True):
        # Update pos
        oldpos = (self.x, self.y)
        self.oldpos = oldpos
        self.pos = [self.x + dx, self.y + dy]
        # Move constraints
        if check_constraints:
            if not self.contained(self.parent):
                self.pos = [oldpos[0], oldpos[1]]
                return
            for brother in self.parent.children:
                if (brother is not self) and (self.collide_widget(brother)):
                    self.pos = oldpos
                    return
        for ch in self.children:
            if isinstance(ch, GenericWidget):
                ch.move(dx, dy, check_constraints=False)

    def resize(self, dx, dy, touch):
        # Update size
        oldsize = (self.size[0], self.size[1])
        oldpos = (self.x, self.y)
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
        if not self.contained(self.parent):
            self.size = oldsize
            self.pos = oldpos
            return
        for brother in self.parent.children:
            if (brother is not self) and (self.collide_widget(brother)):
                self.size = oldsize
                self.pos = oldpos
                return
        for ch in self.children:
            if isinstance(ch, GenericWidget):
                if not ch.contained(self):
                    self.size = oldsize
                    self.pos = oldpos
                    return

    def add(self, touch, item, check_constraints=True):
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

        # Check creation constraints
        if check_constraints:
            if not w.contained(self):
                w.delete()
                return None
            for brother in self.children:
                if (brother is not w) and (w.collide_widget(brother)):
                    w.delete()
                    return None

        touch.grab(w, exclusive=True)
        touch.ud['ppos'] = (touch.x, touch.y)
        touch.ud['mode'] = Mode.RESIZE
        touch.ud['add'] = True
        return w

    def delete(self):
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
                    touch.ud['ppos'] = (touch.x, touch.y)
                    touch.ud['mode'] = Mode.SELECT
                # RESIZE
                elif touch.button == 'right':
                    touch.grab(self, exclusive=True)
                    touch.ud['ppos'] = (touch.x, touch.y)
                    touch.ud['mode'] = Mode.RESIZE
                    touch.ud['add'] = False
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            dx = touch.x - touch.ud['ppos'][0]
            dy = touch.y - touch.ud['ppos'][1]
            touch.ud['ppos'] = (touch.x, touch.y)
            if touch.ud['mode'] == Mode.SELECT:
                self.move(dx, dy)
            if touch.ud['mode'] == Mode.RESIZE:
                self.resize(dx, dy, touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)

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

    def get_formula(self):
        if isinstance(self, AtomWidget):
            return self.text
        if isinstance(self, EllipseWidget):
            conjunction = []
            disjuntion = []
            for ch in self.children:
                if isinstance(ch, SquareWidget):
                    disjuntion.append(ch.get_formula())
                else:
                    conjunction.append(ch.get_formula())
            if conjunction == []:
                conjunction.append('True')
            if disjuntion == []:
                disjuntion.append('False')
            return '(' + '('+string.join(conjunction, ' AND ')+')' + \
                ' IMPLIES ' + '('+string.join(disjuntion, ' OR ')+')' + ')'
        else:
            strs = []
            for ch in self.children:
                strs.append(ch.get_formula())
            if strs == []:
                strs.append('True')
            return '(' + string.join(strs, ' AND ') + ')'

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

class Line:

    def __init__(self, hook, x, y, line_id):
        self.hook_list = [hook]
        self.grabbed_hook = hook
        self.line_id = line_id
        self.canvas = hook.parent.canvas
        self.render = None
        with self.canvas:
            self.render = graphics.Line(points=(x, y), width=2)

    def _get_points_from_hook(self, hook):
        i = 0
        while (self.hook_list[i] != hook):
            i += 1
            if i >= len(self.hook_list):
                return -1
        return i * 2

    def extend(self, x, y):
        pts = self.render.points
        # p = max(self._get_points_from_hook(self.grabbed_hook), 2)
        # if p < 0:
        #     return
        # head_points = self.render.points[:p]
        # tail_points = self.render.points[(p+2):]
        # self.render.points = head_points + [x, y] + tail_points
        extent = len(self.hook_list) * 2 #max(len(pts)-2, 2)
        self.render.points = pts[:extent] + [x, y]

    def append(self, hook):
        self.extend(hook.center_x, hook.center_y)
        self.hook_list.append(hook)

    def move_hook(self, hook):
        p = self._get_points_from_hook(hook)
        if p < 0:
            return
        head_points = self.render.points[:p]
        tail_points = self.render.points[(p+2):]
        x, y = hook.center
        self.render.points = head_points + [x, y] + tail_points

    def delete(self):
        for h in self.hook_list:
            h.line = None
        self.canvas.remove(self.render)

class HookWidget(GenericWidget):

    # Reference to the currently grabbed line
    grabbed_line = None
    line_count = long(0)

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

    def move(self, dx, dy, check_constraints=True):
        super(HookWidget, self).move(dx, dy, check_constraints)
        if self.line:
            self.line.move_hook(self)

    def on_disabled(self, instance, value):
        if value == True:
            self.opacity = 0
            # if self.line:
            #     self.line.delete()
            #     self.line = None
        else:
            self.opacity = 1

    def add_line(self):
        self.line = Line(self, self.center_x, self.center_y,
                         HookWidget.line_count)
        self._toggle_line_item()
        window.Window.bind(mouse_pos=self.on_mouse_pos)
        HookWidget.grabbed_line = self.line
        HookWidget.line_count += 1

    def delete_line(self):
        self.line.delete()

    def attach_line(self):
        if self.line != None:
            return

        # Update line
        self.line = HookWidget.grabbed_line
        self.line.append(self)

        # Cleanup stuff
        window.Window.unbind(mouse_pos=self.line.grabbed_hook.on_mouse_pos)
        HookWidget.grabbed_line = None
        self._toggle_line_item()

    def detach_line(self):
        pass

    def on_mouse_pos(self, obj, value):
        self.line.extend(value[0], value[1])

    def on_touch_down(self, touch, mode=Mode.SELECT, item=Item.ATOM):

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
                    if self.line == None:
                        self.add_line()
                    else:
                        pass
                # DELETE LINE
                elif touch.button == 'right':
                    self.delete_line()
        return True

    # def on_touch_move(self, touch):
    #     if (touch.grab_current is self) and (self.line):
    #         self.line.points = self.line.points[:2] + [touch.x, touch.y]

    # def on_touch_up(self, touch):
    #     print touch.pos
    #     if self.collide_point(*touch.pos) == True:
    #         print self.line

class NexusWidget(HookWidget):

    def __init__(self, **kwargs):
        super(NexusWidget, self).__init__(**kwargs)
        # Init position correction
        self.pos = (self.pos[0] - self.width/2, self.pos[1] - self.height/2)

    def extend_line(self):
        self._toggle_line_item()
        self.line.grabbed_hook = self
        window.Window.bind(mouse_pos=self.on_mouse_pos)
        HookWidget.grabbed_line = self.line

    def on_touch_down(self, touch, mode=Mode.SELECT, item=Item.ATOM):

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
                    if self.line:
                        self.extend_line()
                # DELETE LINE
                elif touch.button == 'right':
                    self.delete_line()
        return True

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

    def delete(self):
        self.atom.unbind(hook_points=self.on_hook_points)
        super(AtomWidget, self).delete()

    def resize(self, dx, dy, touch):
        pass

    def scale(self, factor, origin):
        self.scalefactor *= factor
        previous_size = (self.width, self.height)
        super(AtomWidget, self).scale(factor, origin)
        #if self.size[1] >= self.max_height:
        if self.scalefactor >= self.max_scalefactor:
            self.size = previous_size

    def update(self):
        self.ids.hook_left.disabled = not self._hook_points[0]
        self.ids.hook_right.disabled = not self._hook_points[1]
        self.ids.hook_top.disabled = not self._hook_points[2]
        self.ids.hook_bottom.disabled = not self._hook_points[3]

    def on_hook_points(self, instance, value):
        self._hook_points = value
        if self.show_hooks:
            self.update()

    def print_variables(self):
        if self.ids.hook_left.line:
            print self.ids.hook_left.line.line_id
        if self.ids.hook_right.line:
            print self.ids.hook_right.line.line_id
        if self.ids.hook_top.line:
            print self.ids.hook_top.line.line_id
        if self.ids.hook_bottom.line:
            print self.ids.hook_bottom.line.line_id

class CustomLabel(label.Label):

    def on_texture(self, instance, value):
        print 'texture changed!', instance, value

    def on_touch_down(self, touch, mode=Mode.SELECT, item=Item.ATOM):
        if self.collide_point(*touch.pos) == False:
            return False
        else:
            if mode == Mode.INSERT and touch.button == 'left':
                self.parent.print_variables()
                return True
            else:
                return False

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

    def show_hooks(self):
        AtomWidget.show_hooks = True
        for w in self.walk(restrict=True):
            if isinstance(w, AtomWidget):
                w.update()
            if isinstance(w, NexusWidget):
                w.disabled = False
                w.opacity = 1

    def hide_hooks(self):
        AtomWidget.show_hooks = False
        for w in self.walk(restrict=True):
            if isinstance(w, HookWidget):
                w.disabled = True
                w.opacity = 0

if __name__ == '__main__':
    kwad.attach()
    MainApp().run()
