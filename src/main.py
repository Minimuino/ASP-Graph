# -*- coding: utf-8 -*-

import sys
import os
import string
import cProfile

import kivy.app as app
import kivy.base as base
import kivy.core.window as window
import kivy.graphics as graphics
import kivy.lang as lang
import kivy.properties as prop
import kivy.uix.widget as widget
import kivy.uix.textinput as txt
import kivy.uix.dropdown as drop
import kivy.uix.button as but
import kivy.uix.togglebutton as toggle
import kivy.uix.spinner as spin
import kivy.uix.floatlayout as fl
import kivy.uix.boxlayout as box
import kivy.uix.gridlayout as grid
import kivy.uix.popup as pup
import kivy.animation as anim

sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))
import gringo
import asp_graph as asp
import normalization as norm

class HoverBehavior(object):

    hovered = prop.BooleanProperty(False)
    border_point= prop.ObjectProperty(None)
    '''border_point contains the last relevant point received by the Hoverable.
    This can be used in on_enter or on_leave in order to know where was
    dispatched the event.
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')
        window.Window.bind(mouse_pos=self.on_mouse_pos)
        super(HoverBehavior, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return # do proceed if I'm not displayed <=> If have no parent
        pos = args[1]
        # Next line to_widget allow to compensate for relative layout
        inside = self.collide_point(*self.to_widget(*pos))
        if self.hovered == inside:
            # We have already done what was needed
            return
        self.border_point = pos
        self.hovered = inside
        if inside:
            self.dispatch('on_enter')
        else:
            self.dispatch('on_leave')

    def on_enter(self):
        pass

    def on_leave(self):
        pass

# class MenuButton(but.Button):

#     def __init__(self, **kwargs):
#         self.values = prop.ListProperty([])
#         self.dropdown = drop.DropDown()
#         self.dropdown.add_widget(but.Button(text='u',
#                                             size_hint_y=None, height=44))
#         self.bind(on_release=self.dropdown.open)
#         super(MenuButton, self).__init__(**kwargs)

#     def on_values(self, instance, value):
#         print self.values, instance, value
#         for v in value:
#             self.dropdown.add_widget(but.Button(text=v))
#             print v

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


class MenuItem(widget.Widget):
    '''Background color, in the format (r, g, b, a).'''
    background_color_normal = prop.ListProperty([0.2, 0.2, 0.2, 1])
    background_color_down = prop.ListProperty([0.3, 0.3, 0.3, 1])
    background_color = prop.ListProperty([])
    separator_color = prop.ListProperty([0.8, 0.8, 0.8, 1])
    text_color_hovered = prop.ListProperty([1,1,1,1])
    text_color_unhovered = prop.ListProperty([.7,.7,.7,1])
    inside_group = prop.BooleanProperty(False)
    pass

class MenuSubmenu(MenuItem, spin.Spinner, HoverBehavior):

    def __init__(self, **kwargs):
        self.list_menu_item = []
        super(MenuSubmenu, self).__init__(**kwargs)
        self.dropdown_cls = MenuDropDown

    def add_widget(self, item):
        self.list_menu_item.append(item)
        self.show_submenu()

    def show_submenu(self):
        self.clear_widgets()
        for item in self.list_menu_item:
            item.inside_group = True
            self._dropdown.add_widget(item)

    def _build_dropdown(self, *largs):
        if self._dropdown:
            self._dropdown.unbind(on_dismiss=self._toggle_dropdown)
            self._dropdown.dismiss()
            self._dropdown = None
        self._dropdown = self.dropdown_cls()
        self._dropdown.bind(on_dismiss=self._toggle_dropdown)

    def _update_dropdown(self, *largs):
        pass

    def _toggle_dropdown(self, *largs):
        #print 'Toggle dropdown'
        self.is_open = not self.is_open
        ddn = self._dropdown
        ddn.size_hint_x = None
        if not ddn.container:
            return
        children = ddn.container.children
        if children:
            ddn.width = max(self.width, max(c.width for c in children))
        else:
            ddn.width = self.width
        for item in children:
            item.size_hint_y = None
            item.height = min([self.height, 48])

    def clear_widgets(self):
        self._dropdown.clear_widgets()

class MenuDropDown(drop.DropDown):
    pass

class MenuButton(MenuItem, but.Button, HoverBehavior):

    icon = prop.StringProperty(None, allownone=True)

    def on_release(self):
        print("Button", self.text, "triggered")
        if isinstance(self.parent.parent, MenuDropDown):
            self.parent.parent.dismiss()

class MenuEmptySpace(MenuItem):
    pass

class MenuBar(box.BoxLayout):

    '''Background color, in the format (r, g, b, a).'''
    background_color = prop.ListProperty([0.2, 0.2, 0.2, 1])
    separator_color = prop.ListProperty([0.8, 0.8, 0.8, 1])

    def __init__(self, **kwargs):
        self.itemsList = []
        super(MenuBar, self).__init__(**kwargs)

    def add_widget(self, item, index=0):
        if not isinstance(item, MenuItem):
            raise TypeError("MenuBar accepts only MenuItem widgets")
        super(MenuBar, self).add_widget(item, index)
        if index == 0:
            index = len(self.itemsList)
        self.itemsList.insert(index, item)

class AtomSelectionButton(toggle.ToggleButton):

    def __init__(self, **kwargs):
        super(AtomSelectionButton, self).__init__(**kwargs)

    def on_release(self):
        asp.AtomWidget.atom_name = self.text

class AtomNameInput(txt.TextInput):

    def __init__(self, **kwargs):
        self.root = prop.ObjectProperty(None)
        self.name_list = prop.ObjectProperty(None)
        super(AtomNameInput, self).__init__(**kwargs)

    def on_focus(self, instance, value):
        if value:
            self.root._keyboard_release()

    def on_text_validate(self):
        self.name_list.add_widget(AtomSelectionButton(text=self.text))
        self.text = ''
        self.root._keyboard_catch()

class GlobalContainer(box.BoxLayout):

    graph_list = prop.ListProperty([])
    active_graph = prop.ObjectProperty(None)
    show_sidepanel = prop.BooleanProperty(False)

    def __init__(self, **kwargs):
        super(GlobalContainer, self).__init__(**kwargs)
        self._keyboard = None
        self.request_keyboard()
        self.solver = gringo.Control()

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
            base.stopTouchApp()
        elif keycode[1] == 'e':
            self.active_graph.mode = asp.Mode.EDIT
        elif keycode[1] == 's':
            self.active_graph.mode = asp.Mode.SELECT
        elif keycode[1] == 'r':
            self.active_graph.mode = asp.Mode.RESIZE
        elif keycode[1] == '1':
            self.active_graph.item = asp.Item.ATOM
        elif keycode[1] == '2':
            self.active_graph.item = asp.Item.ELLIPSE
        elif keycode[1] == '3':
            self.active_graph.item = asp.Item.SQUARE
        elif keycode[1] == 'p':
            self.active_graph.show_tree(0)
        elif keycode[1] == 'o':
            print self.active_graph.get_formula()
        elif keycode[1] == 'n':
            self.gringo_query()
        elif keycode[1] == 'g':
            self.show_save()
        elif keycode[1] == 'l':
            self.show_load()
        elif keycode[1] == 'i':
            self.active_graph.export_to_png('diagram.png')
        elif keycode[1] == 't':
            self.toggle_sidepanel()
        return True

    def toggle_sidepanel(self):
        self.show_sidepanel = not self.show_sidepanel
        if self.show_sidepanel:
            width = self.width * .15
        else:
            width = 0
        anim.Animation(width=width, d=.15, t='out_quart').start(
                self.ids.sidepanel)
        if not self.show_sidepanel:
            self.ids.sidepanel.focus = False
            # Also release keyboard
        #self.update_sourcecode()

    def gringo_query(self):
        rpn = self.active_graph.get_formula_RPN()
        print 'RPN formula: ', rpn
        f = norm.Formula(rpn)
        n = f.root
        self.solver = gringo.Control()
        for i in norm.normalization(n):
            #print i
            s = norm.to_asp(i)
            print 'ASP code:'
            print s
            self.solver.add('base', [], s)
        try:
            self.solver.ground([('base', [])])
            result = self.solver.solve(on_model=self.on_model)
            if result == gringo.SolveResult.UNKNOWN:
                print "UNKNOWN"
            elif result == gringo.SolveResult.SAT:
                print "SAT"
            elif result == gringo.SolveResult.UNSAT:
                print "UNSAT"
        except RuntimeError, e:
            print e

    def on_model(self, m):
        print 'Stable models:'
        print m

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
            stream.write('#:kivy 1.0.9\n' + self.active_graph.get_tree(0))
        self.dismiss_popup()

    def load(self, path, filename):
        f = os.path.join(path, filename[0])
        parent = self.active_graph.parent
        # NOTE: Keep this order, it is important for releasing/catching
        # keyboard correctly
        self.dismiss_popup()
        self.active_graph.delete_tree()
        self.active_graph.delete_root()
        parent.add_widget(lang.Builder.load_file(f))


class MainApp(app.App):

    def build(self):
        print 'Building...'

    def on_start(self):
        for w in self.root.walk(restrict=True):
            if isinstance(w, asp.RootWidget):
                GlobalContainer.graph_list = [w]
                GlobalContainer.active_graph = GlobalContainer.graph_list[0]
        self.profile = cProfile.Profile()
        self.profile.enable()

    def on_stop(self):
        self.profile.disable()
        self.profile.dump_stats('myapp.profile')

if __name__ == '__main__':
    MainApp().run()
