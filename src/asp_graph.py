# -*- coding: utf-8 -*-

import sys
import os
import string

import kivy.app as app
import kivy.uix.widget as widget
import kivy.uix.textinput as txt
import kivy.core.window as window
import kivy.graphics as graphics
import kivy.lang as lang
import kivy.properties as prop
import kivy.uix.floatlayout as fl
import kivy.uix.popup as pup

import kwad


# Enum class for drawing modes
class Mode:
    EDIT, SELECT, RESIZE = range(3)

# Enum class for adding objects
class Item:
    ATOM, ELLIPSE, SQUARE = range(3)


class CustomPopup(pup.Popup):

    def __init__(self, root, **kwargs):
        self.root = root
        self.bind(on_open=self.open_callback)
        self.bind(on_dismiss=self.dismiss_callback)
        super(CustomPopup, self).__init__(**kwargs)

    def open_callback(self, instance):
        print 'exec'
        #self.root._keyboard.unbind(on_key_down=self.root._on_keyboard_down)
        self.root._keyboard_release()
        #print('User focused', instance)

    def dismiss_callback(self, instance):
        print 'dismiss'

        # keyboard = self._keyboard
        # if keyboard:
        #     keyboard.unbind(on_key_down=self.keyboard_on_key_down)
        # super(TextWidget, self).hide_keyboard()

        #self.root._keyboard.bind(on_key_down=self.root._on_keyboard_down)
        self.root._keyboard_catch()
        #print('User defocused', instance)

class LoadDialog(fl.FloatLayout):
    load = prop.ObjectProperty(None)
    cancel = prop.ObjectProperty(None)

class SaveDialog(fl.FloatLayout):
    save = prop.ObjectProperty(None)
    text_input = prop.ObjectProperty(None)
    cancel = prop.ObjectProperty(None)

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

    def add(self, touch, item):
        if item == Item.ATOM:
            w = AtomWidget(parent_color=self.color, pos=touch.pos)
        if item == Item.ELLIPSE:
            w = EllipseWidget(default_children=False,
                              parent_color=self.color,
                              pos=(touch.x, touch.y))
        if item == Item.SQUARE:
            if not isinstance(self, EllipseWidget):
                return None
            w = SquareWidget(default_children=False,
                             parent_color=self.color,
                             pos=touch.pos)
        self.add_widget(w)
        touch.grab(w, exclusive=True)
        touch.ud['ppos'] = (touch.x, touch.y)
        touch.ud['mode'] = Mode.RESIZE
        touch.ud['add'] = True
        return w

    def delete(self):
        self.parent.remove_widget(self)

    def on_touch_down(self, touch, mode=Mode.SELECT, item=Item.ATOM):

        if self.collide_point(*touch.pos) == False:
            return False

        for child in self.children[:]:
            if child.dispatch('on_touch_down', touch, mode, item):
                return True

        print self, mode
        if mode ==  Mode.EDIT:
            if 'button' in touch.profile:
                if touch.button == 'left':
                    # ADD
                    self.add(touch, item)
                elif touch.button == 'right':
                    # DELETE
                    self.delete()
                    #print 'Deleting ', self, ' from ', self.parent
        elif mode == Mode.SELECT:
            # MOVE
            if 'button' in touch.profile:
                if touch.button == 'left':
                    touch.grab(self, exclusive=True)
                    touch.ud['ppos'] = (touch.x, touch.y)
                    touch.ud['mode'] = Mode.SELECT
                elif touch.button == 'right':
                    pass
        elif mode == Mode.RESIZE:
            # RESIZE
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

    def show_tree(self, depth):
        if isinstance(self, AtomWidget):
            return 0
        else:
            for ch in self.children:
                print ' '*2*depth, ch
                ch.show_tree(depth+1)
            return 0

    def delete_tree(self):
        if isinstance(self, TextWidget):
            self.delete()
        else:
            for ch in self.children:
                ch.delete_tree()
            self.clear_widgets()

    def get_tree(self, depth):
        strl = []
        strl.append(' '*4*depth + '{0}:'.format(type(self).__name__))
        strl.append(' '*4*(depth+1) + 'pos: {0}'.format(self.pos))
        if (depth % 2) <> 0:
            strl.append(' '*4*(depth+1) + 'color: .800, .800, .800')
        if isinstance(self, AtomWidget):
            strl.append(' '*4*(depth+1) +
                        'init_text: \'{0}\''.format(self.children[0].text))
        else:
            strl.append(' '*4*(depth+1) + 'size: {0}'.format(self.size))
            for ch in self.children:
                strl.append(ch.get_tree(depth+1))
        return string.join(strl, '\n')

    def get_formula(self):
        if isinstance(self, AtomWidget):
            return self.children[0].text
        if isinstance(self, EllipseWidget):
            conjunction = []
            disjuntion = []
            for ch in self.children:
                if isinstance(ch, SquareWidget):
                    disjuntion.append(ch.get_formula())
                else:
                    conjunction.append(ch.get_formula())
            return '(' + '('+string.join(conjunction, ' AND ')+')' + \
                ' IMPLIES ' + '('+string.join(disjuntion, ' OR ')+')' + ')'
        else:
            strs = []
            for ch in self.children:
                strs.append(ch.get_formula())
            return '(' + string.join(strs, ' AND ') + ')'

class AtomWidget(GenericWidget):

    def __init__(self, **kwargs):
        super(AtomWidget, self).__init__(**kwargs)
        # Init position correction
        self.pos = (self.pos[0] - self.size[0]/2, self.pos[1] - self.size[1]/2)

class TextWidget(txt.TextInput, GenericWidget):

    def __init__(self, **kwargs):
        super(TextWidget, self).__init__(**kwargs)
        self.bind(focus=self.on_focus)
        self.root = None

    def on_focus(self, instance, value):

        if not self.root:
            for w in self.walk_reverse(loopback=True):
                if isinstance(w, RootWidget):
                    self.root = w
        if value:
            #self.root._keyboard.unbind(on_key_down=self.root._on_keyboard_down)
            self.root._keyboard_release()
            #print('User focused', instance)
        else:
            keyboard = self._keyboard
            if keyboard:
                keyboard.unbind(on_key_down=self.keyboard_on_key_down)
            super(TextWidget, self).hide_keyboard()
            #self.root._keyboard.bind(on_key_down=self.root._on_keyboard_down)
            self.root._keyboard_catch()
            #print('User defocused', instance)

    def on_touch_down(self, touch, mode=Mode.SELECT, item=Item.ATOM):
        if self.collide_point(*touch.pos) == False:
            return False
        else:
            if mode == Mode.EDIT and touch.button == 'left':
                super(TextWidget, self).on_touch_down(touch)
                return True
            else:
                return False

    def move(self, dx, dy, check_constraints):
        pass

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
        self._keyboard = None
        self.request_keyboard()
        self.mode = Mode.EDIT
        self.item = Item.ATOM

        # Nasty patch to solve a problem with color when the first widget
        # is added. Simply add and remove a widget in order to let kivy
        # load some stupid object properties.
        w = EllipseWidget(default_children=True,
                          parent_color=self.color,
                          pos=(0, 0))
        self.add_widget(w)
        self.remove_widget(w)
        print self.color

    def request_keyboard(self):
        self._keyboard = window.Window.request_keyboard(self._keyboard_release,
                                                        self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_catch(self):
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_release(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        #self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'q':
            sys.exit()
        elif keycode[1] == 'e':
            self.mode = Mode.EDIT
        elif keycode[1] == 's':
            self.mode = Mode.SELECT
            print 'hola!', self
        elif keycode[1] == 'r':
            self.mode = Mode.RESIZE
        elif keycode[1] == '1':
            self.item = Item.ATOM
        elif keycode[1] == '2':
            self.item = Item.ELLIPSE
        elif keycode[1] == '3':
            self.item = Item.SQUARE
        elif keycode[1] == 'p':
            self.show_tree(0)
        elif keycode[1] == 'o':
            print self.get_formula()
        elif keycode[1] == 'g':
            self.show_save()
        elif keycode[1] == 'l':
            self.show_load()
        return True

    def move(self, dx, dy):
        pass

    def resize(self, dx, dy, touch):
        pass

    def delete(self):
        pass

    def delete_root(self):
        self._keyboard_release()
        self.parent.remove_widget(self)

    def on_touch_down(self, touch):
        super(RootWidget, self).on_touch_down(touch, self.mode, self.item)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = CustomPopup(self, title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def show_save(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = CustomPopup(self, title="Save file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def save(self, path, filename):
        with open(os.path.join(path, filename), 'w') as stream:
            stream.write('#:kivy 1.0.9\n' + self.get_tree(0))
        self.dismiss_popup()

    def load(self, path, filename):
        f = os.path.join(path, filename[0])
        parent = self.parent
        # NOTE: Keep this order, it is important for releasing/catching
        # keyboard correctly
        self.dismiss_popup()
        self.delete_tree()
        self.delete_root()
        parent.add_widget(lang.Builder.load_file(f))


class MainApp(app.App):

    def build(self):
        return RootWidget()
        return lang.Builder.load_file('savedata.kv')

if __name__ == '__main__':
    kwad.attach()
    MainApp().run()
