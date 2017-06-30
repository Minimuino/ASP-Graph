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

import sys
import os
import string
import re

from kivy.config import Config
Config.set('graphics', 'width', '1024')
Config.set('graphics', 'height', '680')

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

import asp_graph as asp
import normalization as norm
import solver as eg_solver
import tutorial
from name_manager import NameManager, NameParser

__title__ = "ASP-Graph"
__author__ = "Carlos Pérez Ramil"
__copyright__ = "Copyright 2017, Carlos Pérez Ramil <c.pramil at udc.es>"
__license__ = "GNU General Public License - Version 3"
__version__ = "0.0.1"

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
    """border_point contains the last relevant point received by the Hoverable.
    This can be used in on_enter or on_leave in order to know where was
    dispatched the event.
    """

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

    def __init__(self, root, catch_keyboard=True, **kwargs):
        self.root = root
        self.catch_keyboard = catch_keyboard
        self.bind(on_open=self.open_callback)
        self.bind(on_dismiss=self.dismiss_callback)
        super(CustomPopup, self).__init__(**kwargs)
        self.auto_dismiss = False

    def open_callback(self, instance):
        print 'exec'
        #self.root._keyboard.unbind(on_key_down=self.root._on_keyboard_down)
        if self.catch_keyboard:
            self.root._keyboard_release()
        #print('User focused', instance)

    def dismiss_callback(self, instance):
        print 'dismiss'

        # keyboard = self._keyboard
        # if keyboard:
        #     keyboard.unbind(on_key_down=self.keyboard_on_key_down)
        # super(TextWidget, self).hide_keyboard()

        #self.root._keyboard.bind(on_key_down=self.root._on_keyboard_down)
        if self.catch_keyboard:
            self.root._keyboard_catch()
        #print('User defocused', instance)

class TextInputDialog(fl.FloatLayout):
    validate_callback = prop.ObjectProperty(None)
    cancel = prop.ObjectProperty(None)

    def __init__(self, caption='',
                 validate_callback=None,
                 dismiss_on_validate=True,
                 focus=True,
                 **kwargs):
        super(TextInputDialog, self).__init__(**kwargs)
        self.ids.textinput.hint_text = caption
        self.ids.textinput.focus = focus
        self.dismiss_on_validate = dismiss_on_validate
        self.validate_callback = validate_callback

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

class StableModelDialog(fl.FloatLayout):
    cancel = prop.ObjectProperty(None)

    def __init__(self, solver, **kwargs):
        super(StableModelDialog, self).__init__(**kwargs)
        self.solver = solver
        self.index = 0
        number = [str(self.index+1), str(len(self.solver.get_models()))]
        self.ids.number.text = '/'.join(number)

    def previous_model(self):
        if self.index < 1:
            return
        self.index -= 1
        model = self.solver.get_models()[self.index]
        self.solver.generate_graph(model)
        self.ids.img.reload()
        number = [str(self.index+1), str(len(self.solver.get_models()))]
        self.ids.number.text = '/'.join(number)

    def next_model(self):
        models = self.solver.get_models()
        if self.index > (len(models) - 2):
            return
        self.index += 1
        model = models[self.index]
        self.solver.generate_graph(model)
        self.ids.img.reload()
        number = [str(self.index+1), str(len(models))]
        self.ids.number.text = '/'.join(number)

class ErrorDialog(fl.FloatLayout):
    cancel = prop.ObjectProperty(None)

    def __init__(self, str_err, **kwargs):
        super(ErrorDialog, self).__init__(**kwargs)
        self.ids.label.text = str_err

class AboutDialog(fl.FloatLayout):
    cancel = prop.ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AboutDialog, self).__init__(**kwargs)
        self.ids.title.text = __title__
        self.ids.version.text = 'Version ' + __version__
        self.ids.copyright.text = __copyright__
        self.ids.license.text = __license__

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

class CustomButton(MenuItem, but.Button):
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

    def on_touch_down(self, touch):
        # This is a workaround in order to bypass scrolling functions and
        # fire MenuButton on_release() method always, even when the click
        # is done while the mouse is moving over the button.
        # (DropDown extends Scrollview)
        self.simulate_touch_down(touch)
        super(MenuDropDown, self).on_touch_down(touch)
        return True

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
        if self.parent is None:
            return

        if self.state == 'down':
            asp.AtomWidget.active_atom = NameManager.Instance().get(self.text)
            self.parent.update_atom_editor(self.text)
            self.parent.set_item('atom')
        else:
            asp.AtomWidget.active_atom = None
            self.parent.update_atom_editor('')


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
        self.ids.constant_checkbox.state = states[atom.is_constant]

    def update_atom(self):
        is_constant = self.ids.constant_checkbox.state == 'down'
        hook_points = [self.ids.hook_left.state == 'down',
                       self.ids.hook_right.state == 'down',
                       self.ids.hook_top.state == 'down',
                       self.ids.hook_bottom.state == 'down']
        self.root.update_atom(self.ids.hook_label.text,
                              new_hook_points=hook_points,
                              is_constant=is_constant)

class GlobalContainer(box.BoxLayout):

    graph_list = prop.ListProperty([])
    active_graph = prop.ObjectProperty(None)
    name_manager = NameManager.Instance()
    show_sidepanel = prop.BooleanProperty(True)
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
        self.working_dir = './'
        self.tutorial = None
        self.popup_stack = []
        window.Window.bind(on_resize=self.on_resize)

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
        if keycode[1] == 'escape':
            base.stopTouchApp()
        elif keycode[1] == 'd':
            self.set_mode('insert')
        elif keycode[1] == 's':
            self.set_mode('select')
        elif keycode[1] == 'w':
            self.set_item('atom')
        elif keycode[1] == 'e':
            self.set_item('ellipse')
        elif keycode[1] == 'r':
            self.set_item('rectangle')
        elif keycode[1] == 'p':
            self.active_graph.show_tree(0)
        elif keycode[1] == 'o':
            self.view_symbolic_formula()
        elif keycode[1] == 'n':
            self.show_gringo_query()
        elif keycode[1] == 'g':
            self.show_save()
        elif keycode[1] == 'l':
            self.show_load()
        elif keycode[1] == 'y':
            print self.name_manager.get_all()
            print asp.Line.get_all_lines()
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

    def _focus_name_list(self, value):
        if value and (asp.AtomWidget.active_atom is not None):
            previous_name = asp.AtomWidget.active_atom.name
            for button in self.ids.name_list.children:
                if (button.text == previous_name) and (button.state != 'down'):
                    button.trigger_action()
        elif value:
            if self.ids.name_list.children:
                self.ids.name_list.children[-1].trigger_action()
        else:
            for button in self.ids.name_list.children:
                if button.state == 'down':
                    button.trigger_action()

    def on_resize(self, window, width, height):
        if self.show_sidepanel:
            self.ids.sidepanel.width = self.width * .15
        self.active_graph.size = self.ids.stencilview.size

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

    def update_atom_editor(self, name):
        editor = self.ids.atom_editor
        if name == '':
            editor.disabled = True
        else:
            if editor.disabled:
                editor.disabled = False
            atom = self.name_manager.get(name)
            editor.update(atom)

    def update_atom(self, name, new_name='', new_hook_points=[], is_constant=False):
        atom = self.name_manager.get(name)
        if new_name <> '':
            atom.name = new_name
        if len(new_hook_points) == 4:
            atom.hook_points = new_hook_points
            # print id(atom.hook_points)
        atom.is_constant = is_constant

    def register_atom(self, name,
                      hooks=[False, False, False, False], is_constant=False):
        if name == '':
            return
        children = self.ids.name_list.children
        new_button = None
        name_to_insert = name
        i = len(children) - 1

        # If the name doesn't exist, register atom
        if self.name_manager.get(name) is None:
            self.name_manager.register(name, asp.Atom(name, hooks, is_constant))
            # print id(self.name_manager.get(name).hook_points)

        # Insert in name_list sorted by name
        while i >= 0:
            if children[i].text < name_to_insert:
                #print children[i].text, '<',  name_to_insert
                pass
            elif children[i].text == name_to_insert:
                # Already exists
                if children[i].state != 'down':
                    children[i].trigger_action()
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
            asp.AtomWidget.active_atom = self.name_manager.get(name)
            self.update_atom_editor(name)
            self.set_item('atom')
        else:
            new_button.trigger_action()

    def rename_atom(self, new_name):
        old_name = ''
        for button in self.ids.name_list.children:
            if button.state == 'down':
                old_name = button.text
                selected_button = button
        if (old_name != '') and (new_name != ''):
            try:
                atom = self.name_manager.get(old_name)
                exists = self.name_manager.get(new_name)
                assert atom is not None
                assert exists is None
            except AssertionError:
                #self.show_error('Name already exists.')
                print 'Name already exists.'
                return
            selected_button.text = new_name
            atom.name = new_name
            self.name_manager.unregister(old_name)
            self.name_manager.register(new_name, atom)
            self.update_atom_editor(new_name)

    def delete_atom(self):
        for button in self.ids.name_list.children:
            if button.state == 'down':
                self.name_manager.unregister(button.text)
                self.active_graph.delete_atom(button.text)
                asp.AtomWidget.active_atom = None
                self.ids.name_list.remove_widget(button)
                self.update_atom_editor('')

    def clear_atoms(self):
        self.ids.name_list.clear_widgets()
        self.name_manager.clear()
        self.update_atom_editor('')
        asp.AtomWidget.active_atom = None

    def new_graph(self):
        # TODO: Migrate to tab system
        asp.Line.clear_lines()
        self.clear_atoms()
        if self.active_graph is None:
            g = asp.RootWidget()
            self.graph_list.append(g)
            self.active_graph = g
            self.ids.stencilview.add_widget(g)
        else:
            self.active_graph.delete_tree()

    def close_graph(self):
        if self.active_graph is not None:
            asp.Line.clear_lines()
            self.active_graph.delete_tree()
            self.active_graph.delete_root()
            self.clear_atoms()
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
        except AttributeError:
            pass
        if item == 'atom':
            self._focus_name_list(True)
        else:
            self._focus_name_list(False)

    def push_popup(self, popup):
        self.popup_stack.append(popup)
        popup.open()

    def dismiss_popup(self):
        popup = self.popup_stack.pop()
        popup.dismiss()

    def show_rename_atom(self):
        content = TextInputDialog(caption="Enter new name",
                                  validate_callback=self.rename_atom,
                                  cancel=self.dismiss_popup)
        p = CustomPopup(self, title="Rename atom", content=content,
                        size_hint=(0.4, 0.25))
        self.push_popup(p)

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        content.ids.filechooser.path = self.working_dir
        p = CustomPopup(self, title="Load file", content=content,
                        size_hint=(0.9, 0.9))
        self.push_popup(p)

    def show_save(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        content.ids.filechooser.path = self.working_dir
        p = CustomPopup(self, title="Save file", content=content,
                        size_hint=(0.9, 0.9))
        self.push_popup(p)

    def show_export(self):
        content = ExportDialog(export=self.export, cancel=self.dismiss_popup)
        content.ids.filechooser.path = self.working_dir
        p = CustomPopup(self, title="Export file", content=content,
                        size_hint=(0.9, 0.9))
        self.push_popup(p)

    def show_gringo_query(self):
        caption = "Enter desired predicates separated by commas"
        content = TextInputDialog(caption=caption,
                                  validate_callback=self.gringo_query,
                                  dismiss_on_validate=False,
                                  focus=False,
                                  cancel=self.dismiss_popup)
        p = CustomPopup(self, title="Output predicates", content=content,
                        size_hint=(0.4, 0.25))
        self.push_popup(p)

    def show_stable_models(self, solver):
        models = solver.get_models()
        content = None
        if len(models) == 0:
            content = ErrorDialog('Unsatisfiable', cancel=self.dismiss_popup)
        else:
            solver.generate_graph(models[0])
            content = StableModelDialog(solver, cancel=self.dismiss_popup)
            content.ids.img.reload()
        p = CustomPopup(self, catch_keyboard=False, title="Stable Models",
                        content=content, size_hint=(0.9, 0.9))
        self.push_popup(p)

    def show_error(self, err_str):
        content = ErrorDialog(err_str, cancel=self.dismiss_popup)
        p = CustomPopup(self, catch_keyboard=False, title="Error",
                        content=content, size_hint=(0.4, 0.3))
        self.push_popup(p)

    def show_about(self):
        content = AboutDialog(cancel=self.dismiss_popup)
        p = CustomPopup(self, catch_keyboard=False, title="About "+__title__,
                        content=content, size_hint=(0.5, 0.5))
        self.push_popup(p)

    def load(self, path, filename):
        self.close_graph()
        self.working_dir = path

        try:
            f = os.path.join(path, filename[0])
            # Temporal line storage. Its contents are arranged as follows:
            # { line_id: (graph, hook_list) , ... }
            lines = {}
            with open(f, 'r') as stream:
                for line in stream:
                    if line.startswith(NameParser.TOKENS['name']):
                        name, hooks, is_constant = NameParser.parse_name(line)
                        self.register_atom(name, hooks, is_constant)
                    if line.startswith(NameParser.TOKENS['line']):
                        line_id, graph = NameParser.parse_line(line)
                        lines[line_id] = (graph, [None] * len(graph))

            new_graph = lang.Builder.load_file(f)
            self.ids.stencilview.add_widget(new_graph)
            self.active_graph = new_graph
            #self.graph_list.pop()
            self.graph_list.append(new_graph)
            for w in self.active_graph.walk(restrict=True):
                if isinstance(w, asp.AtomWidget):
                    w._deferred_init()
                    for i in w.get_line_info():
                        line_id = i[0]
                        hook_index = i[1]
                        lines[line_id][1][hook_index] = i[2]
                elif isinstance(w, asp.NexusWidget):
                    for i in w.line_info:
                        line_id = i[0]
                        hook_index = i[1]
                        lines[line_id][1][hook_index] = w

            for line, info in lines.iteritems():
                print line, info
                asp.Line.build_from_graph(info[0], info[1])

            self.set_mode(self.modestr)
            self.set_item(self.itemstr)
            self.dismiss_popup()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.dismiss_popup()
            self.close_graph()
            self.new_graph()
            self.show_error('Corrupted file.')

    def save(self, path, filename):
        self.working_dir = path
        with open(os.path.join(path, filename), 'w') as stream:
            stream.write('#:kivy 1.0.9\n\n')
            for (name, atom) in self.name_manager.get_all():
                stream.write(NameParser.get_name_str(name, atom.hook_points,
                                                     atom.is_constant))
            for line in asp.Line.get_all_lines():
                stream.write(NameParser.get_line_str(line.line_id,
                                                     line.get_full_graph()))
            stream.write('\n')
            stream.write(self.active_graph.get_tree(0))
        self.dismiss_popup()

    def export(self, path, filename):
        _, ext = os.path.splitext(filename)
        if ext == '.png':
            self.active_graph.export_to_png(os.path.join(path, filename))
        elif ext == '.lp':
            rpn = self.active_graph.get_formula_RPN()
            constants = self.active_graph.get_constants()
            solver = eg_solver.Solver()
            solver.set_formula(rpn, constants)
            rules = solver.generate_asp_rules()
            with open(os.path.join(path, filename), 'w') as stream:
                for r in rules:
                    stream.write(r)
                    stream.write('\n')
        else:
            error_str = 'File extension not supported.'
            print error_str
            self.show_error(error_str)
            return
        self.dismiss_popup()

    def highlight_variables(self):
        self.active_graph.highlight_variables()

    def view_symbolic_formula(self):
        print self.active_graph.get_formula()

    def gringo_query(self, show_predicates):
        def generate_show_statements(predicates):
            pred_list = predicates.split(',')
            pred_list = map(lambda s: s.strip(), pred_list)
            n_args = (lambda name:
                      self.name_manager.get(name).hook_points.count(True))
            pred_list = [p + '/' + str(n_args(p)) for p in pred_list]
            show_list = ['#show {0}.'.format(p) for p in pred_list]
            return show_list

        self.dismiss_popup()

        rpn = self.active_graph.get_formula_RPN()
        rpn = norm.LIT.TRUE if rpn == '' else rpn
        constants = self.active_graph.get_constants()
        print 80 * '-'
        print 'RPN formula:\n', rpn

        solver = eg_solver.Solver()
        result = ''
        try:
            show_statements = []
            if show_predicates:
                try:
                    show_statements = generate_show_statements(show_predicates)
                except Exception:
                    pass
            solver.set_formula(rpn, constants)
            result = solver.solve(show=show_statements)
        except norm.MalformedFormulaError:
            self.show_error('Malformed formula.')
            return
        except RuntimeError, e:
            print e
            self.show_error(str(e))
            return
        self.show_stable_models(solver)

    def begin_tutorial(self):
        if self.tutorial is not None:
            self.tutorial.end()
        else:
            self.tutorial = tutorial.Tutorial(end_callback=self.end_tutorial)
            self.parent.add_widget(self.tutorial)

    def end_tutorial(self):
        self.tutorial = None

class MainApp(app.App):

    title = __title__

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
