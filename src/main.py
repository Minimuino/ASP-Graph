# -*- coding: utf-8 -*-

import sys
import os
import string
import re

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
import kivy.uix.label as lab
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

DEBUG = False
if DEBUG:
    import kwad
    import cProfile
    from pympler import muppy
    from pympler import summary
    from pympler import refbrowser
    from pympler.classtracker import ClassTracker

class HoverBehavior(object):

    hovered = prop.BooleanProperty(False)
    hover_on_children = prop.BooleanProperty(False)
    border_point = prop.ObjectProperty(None)
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
        if self.hover_on_children:
            for w in self.children: #w in self.walk(restrict=True):
                inside |= w.collide_point(*w.to_widget(*pos))
        if self.hovered == inside:
            # We have already done what was needed
            return
        self.border_point = pos
        self.hovered = inside
        if inside:
            self.dispatch('on_enter')
        else:
            self.dispatch('on_leave')

    def activate_hover(self):
        window.Window.bind(mouse_pos=self.on_mouse_pos)

    def deactivate_hover(self):
        window.Window.unbind(mouse_pos=self.on_mouse_pos)

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

class ExportDialog(fl.FloatLayout):
    export = prop.ObjectProperty(None)
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
        self.deactivate_hover()

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

    def add_widget(self, item):
        if isinstance(item, MenuButton):
            item.menubar = self.parent
        self.list_menu_item.append(item)
        self.show_submenu()

    def show_submenu(self):
        self.clear_widgets()
        for item in self.list_menu_item:
            item.inside_group = True
            self._dropdown.add_widget(item)

    def close(self):
        if self.is_open:
            self._dropdown.dismiss()

    def clear_widgets(self):
        self._dropdown.clear_widgets()

    def on_enter(self):
        if self.parent.selected:
            self.parent.close_all_menus()
            if not self.is_open:
                self._toggle_dropdown()

class MenuDropDown(drop.DropDown):
    pass

class MenuButton(MenuItem, but.Button, HoverBehavior):

    icon = prop.StringProperty(None, allownone=True)
    menubar = prop.ObjectProperty(None)

    def on_release(self):
        print("Button", self.text, "triggered")
        if isinstance(self.parent.parent, MenuDropDown):
            self.menubar.selected = False
            self.parent.parent.dismiss()

class MenuLabel(MenuItem, lab.Label):
    pass

class MenuEmptySpace(MenuItem):
    pass

class MenuBar(box.BoxLayout):

    '''Background color, in the format (r, g, b, a).'''
    background_color = prop.ListProperty([0.2, 0.2, 0.2, 1])
    separator_color = prop.ListProperty([0.8, 0.8, 0.8, 1])
    selected = prop.BooleanProperty(False)

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

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) == False:
            self.selected = False
        else:
            self.selected = True
        super(MenuBar, self).on_touch_down(touch)

    def on_selected(self, instance, value):
        for w in self.children:
            if isinstance(w, MenuSubmenu):
                if value:
                    w.activate_hover()
                else:
                    w.deactivate_hover()

    def close_all_menus(self):
        for ch in self.children:
            if isinstance(ch, MenuSubmenu):
                ch.close()

class AtomSelectionButton(toggle.ToggleButton):

    def __init__(self, **kwargs):
        super(AtomSelectionButton, self).__init__(**kwargs)

    def on_release(self):
        if self.state == 'down':
            asp.AtomWidget.active_atom = GlobalContainer.atom_dict[self.text]
            self.parent.update_hook_editor(self.text)
        else:
            asp.AtomWidget.active_atom = None


class AtomNameInput(txt.TextInput):

    valid_name = re.compile('^[_]*[a-z][A-Za-z0-9_\']*$')

    def __init__(self, **kwargs):
        self.root = prop.ObjectProperty(None)
        self.name_list = prop.ObjectProperty(None)
        super(AtomNameInput, self).__init__(**kwargs)

    def on_focus(self, instance, value):
        if value:
            self.root._keyboard_release()

    def insert_text(self, substring, from_undo=False):
        # Validate new substring input
        # Underscores are now ignored and later proccessed in on_text_validate
        s = ''
        if substring == '_':
            s = substring
        else:
            m = self.valid_name.match(self.text[0:self.cursor_col] +
                                      substring + self.text[self.cursor_col:])
            if m <> None:
                s = substring
        return super(AtomNameInput, self).insert_text(s, from_undo=from_undo)

    def on_text_validate(self):
        if self.valid_name.match(self.text):
            self.root.register_atom(self.text)
            self.text = ''
        self.root._keyboard_catch()

class AtomEditor(box.BoxLayout):

    def update(self, atom):
        states = {True: 'down', False: 'normal'}
        self.ids.hook_label.text = atom.name
        self.ids.hook_left.state = states[atom.hook_points[0]]
        self.ids.hook_right.state = states[atom.hook_points[1]]
        self.ids.hook_top.state = states[atom.hook_points[2]]
        self.ids.hook_bottom.state = states[atom.hook_points[3]]

    def update_atom(self):
        hook_points = [False, False, False, False]
        if self.ids.hook_left.state == 'down':
            hook_points[0] = True
        if self.ids.hook_right.state == 'down':
            hook_points[1] = True
        if self.ids.hook_top.state == 'down':
            hook_points[2] = True
        if self.ids.hook_bottom.state == 'down':
            hook_points[3] = True
        self.root.update_atom(self.ids.hook_label.text,
                              new_hook_points=hook_points)

class GlobalContainer(box.BoxLayout):

    graph_list = prop.ListProperty([])
    active_graph = prop.ObjectProperty(None)
    atom_dict = {}
    show_sidepanel = prop.BooleanProperty(False)
    modestr = prop.StringProperty('insert')
    itemstr = prop.StringProperty('atom')

    modes = {'insert': asp.Mode.INSERT,
             'select': asp.Mode.SELECT}
    items = {'atom': asp.Item.ATOM,
             'ellipse': asp.Item.ELLIPSE,
             'rectangle': asp.Item.SQUARE}

    def __init__(self, **kwargs):
        super(GlobalContainer, self).__init__(**kwargs)
        self._keyboard = None
        self.request_keyboard()
        self.solver = gringo.Control()

        if DEBUG:
            self.tracker = ClassTracker()
            self.tracker.track_object(MenuButton)
            self.all_objects = muppy.get_objects()

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
            self.set_mode('insert')
        elif keycode[1] == 's':
            self.set_mode('select')
        elif keycode[1] == '1':
            self.set_item('atom')
        elif keycode[1] == '2':
            self.set_item('ellipse')
        elif keycode[1] == '3':
            self.set_item('rectangle')
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
        elif keycode[1] == 't':
            self.toggle_sidepanel()
        elif keycode[1] == 'tab':
            if not self.show_sidepanel:
                self.toggle_sidepanel()
            self.ids.atom_input.focus = True
        elif keycode[1] == '.':
            if DEBUG:
                rb = refbrowser.InteractiveBrowser(self)
                rb.main()

                # self.all_objects = muppy.get_objects()
                # sum1 = summary.summarize(self.all_objects)
                # summary.print_(sum1)

                # self.tracker.create_snapshot()
                # self.tracker.stats.print_summary()
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

    def update_hook_editor(self, name):
        atom = self.atom_dict[name]
        self.ids.atom_editor.update(atom)

    def update_atom(self, name, new_name='', new_hook_points=[]):
        atom = self.atom_dict[name]
        if new_name <> '':
            atom.name = new_name
        if len(new_hook_points) == 4:
            atom.hook_points = new_hook_points
            # print id(atom.hook_points)

    def register_atom(self, name):
        if name == '':
            return
        children = self.ids.name_list.children
        new_button = None
        name_to_insert = name
        i = len(children) - 1

        # Register atom
        self.atom_dict[name] = asp.Atom(name, [False, False, False, False])
        # print id(self.atom_dict[name].hook_points)

        # Insert in name_list sorted by name
        while i >= 0:
            if children[i].text < name_to_insert:
                #print children[i].text, '<',  name_to_insert
                pass
            elif children[i].text == name_to_insert:
                # Already exists
                #print children[i].text, '==',  name_to_insert
                return
            elif children[i].text > name_to_insert:
                #print children[i].text, '>',  name_to_insert
                temp = children[i].text
                children[i].text = name_to_insert
                name_to_insert = temp
                if new_button == None:
                    new_button = children[i]
            i -= 1

        self.ids.name_list.add_widget(AtomSelectionButton(text=name_to_insert))
        if new_button == None:
            new_button = children[0]
        if new_button.state == 'down':
            asp.AtomWidget.active_atom = self.atom_dict[name]
            self.update_hook_editor(name)
        else:
            new_button.trigger_action()

    def delete_atom(self):
        for button in self.ids.name_list.children:
            if button.state == 'down':
                self.atom_dict.pop(button.text)
                self.active_graph.delete_atom(button.text)
                asp.AtomWidget.active_atom = None
                self.ids.name_list.remove_widget(button)

    def clear_atoms(self):
        self.ids.name_list.clear_widgets()

    def new_graph(self):
        self.active_graph.delete_tree()
        self.clear_atoms()
        # TODO: Migrate to tab system
        # g = asp.RootWidget()
        # self.graph_list.append(g)
        # self.active_graph = g
        # # do tabs stuff
        # self.ids.stencilview.add_widget(g)

    def close_graph(self):
        self.active_graph.delete_tree()
        self.active_graph.delete_root()
        self.graph_list.pop()
        self.active_graph = None

    def set_mode(self, mode):
        try:
            prev_mode = self.active_graph.mode
            new_mode = self.modes[mode]
            if new_mode == asp.Mode.INSERT:
                self.active_graph.show_hooks()
            else:
                if prev_mode == asp.Mode.INSERT:
                    self.active_graph.hide_hooks()
            self.active_graph.mode = new_mode
            self.modestr = mode
        except KeyError as err:
            print 'ERROR: Invalid mode {0} requested.'.format(str(err))

    def set_item(self, item):
        try:
            self.active_graph.item = self.items[item]
            self.itemstr = item
        except KeyError as err:
            print 'ERROR: Invalid item {0} requested.'.format(str(err))

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

    def show_export(self):
        content = ExportDialog(export=self.export, cancel=self.dismiss_popup)
        self._popup = CustomPopup(self, title="Export file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        f = os.path.join(path, filename[0])
        self.dismiss_popup()
        self.close_graph()
        self.clear_atoms()
        new_graph = lang.Builder.load_file(f)
        self.ids.stencilview.add_widget(new_graph)
        self.active_graph = new_graph
        #self.graph_list.pop()
        self.graph_list.append(new_graph)
        for w in self.active_graph.walk(restrict=True):
            if isinstance(w, asp.AtomWidget):
                self.register_atom(w.text)

    def save(self, path, filename):
        with open(os.path.join(path, filename), 'w') as stream:
            stream.write('#:kivy 1.0.9\n' + self.active_graph.get_tree(0))
        self.dismiss_popup()

    def export(self, path, filename):
        _, ext = os.path.splitext(filename)
        if ext == '.png':
            self.active_graph.export_to_png(os.path.join(path, filename))
        elif ext == '.lp':
            rpn = self.active_graph.get_formula_RPN()
            f = norm.Formula(rpn)
            n = f.root
            with open(os.path.join(path, filename), 'w') as stream:
                for i in norm.normalization(n):
                    s = norm.to_asp(i)
                    stream.write(s)
        else:
            print 'File extension not supported.'
        self.dismiss_popup()

    def gringo_query(self):
        rpn = self.active_graph.get_formula_RPN()
        print 'RPN formula: ', rpn
        f = norm.Formula(rpn)
        n = f.root
        self.solver = gringo.Control()
        for i in norm.normalization(n):
            #print i
            s = norm.to_asp(i)
            print 'ASP RULE: ', s
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

class MainApp(app.App):

    def build(self):
        print 'Building...'

    def on_start(self):
        for w in self.root.walk(restrict=True):
            if isinstance(w, asp.RootWidget):
                GlobalContainer.graph_list = [w]
                GlobalContainer.active_graph = GlobalContainer.graph_list[0]
        if DEBUG:
            self.profile = cProfile.Profile()
            self.profile.enable()

    def on_stop(self):
        if DEBUG:
            self.profile.disable()
            self.profile.dump_stats('asp_graph.profile')

if __name__ == '__main__':
    if DEBUG:
        kwad.attach()
    MainApp().run()
