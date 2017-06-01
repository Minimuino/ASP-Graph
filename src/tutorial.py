# -*- coding: utf-8 -*-

from kivy.lang import Builder
import kivy.uix.bubble as bub

Builder.load_string('''
<Tutorial>:
    id: container
    size_hint: None, None
    width: button.texture_size[0] + 40
    height: button.texture_size[1] + 40
    BubbleButton:
        id: button
        text: 'Tutorial'
        background_color: 0, 0, 0, .5
        on_release: container.on_release()
''')

class Tutorial(bub.Bubble):

    msgs = ['''This is the Canvas.\nIt's the place where you draw a graph
            \n(Click here to continue)''',
            '''Here you can see\nthe current Mode and Item''',
            '''Switch mode with 'S'' and 'D\'''',
            '''Switch item with 'W', 'E' and 'R\'''',
            '''Now choose Ellipse Item
            by pressing 'E\'''',  #Canvas
            '''Left-click and drag on the Canvas
            to draw an Ellipse''',
            '''Now choose Rectangle Item
            by pressing 'R\'''',
            '''Left-click and drag inside the\nEllipse to draw a Rectangle''',
            '''Rectangles can only be\ndrawn within an Ellipse''',
            ('''Zooming and Panning can be done by scrolling or\n'''
             '''clicking the middle mouse button, respectively'''),
            '''Here you can introduce\nnew atom names''',  #Side panel
            '''Now type some name\nin the text box and hit 'Enter\'''',
            '''You've got a new\nname available''',
            '''Left-click anywhere in\nthe Canvas to draw an Atom''',  #Canvas again
            ("You can move around things\nby entering Select Mode (Press 'S')\n"
             "and dragging with Left Mouse Button."),
            '''You can resize Ellipses and Rectangles\ndragging with Right Mouse Button''',
            '''Now enter Insert mode again by pressing 'D\'''',
            ('''Here you can enable/disable the Hooks of an Atom\n'''
             '''A Hook is a little circle to which you can attach a Line'''),  #Lines
            ('''Add a new Line by left-clicking on an\nenabled Hook. '''
             '''Then click again on the canvas to create a Nexus,\n'''
             '''or on another Hook to attach the current Line to it'''),
            '''Also, you can delete an item by right-clicking on it in Insert Mode''',
            ('''If you right-click on a Hook, the Line will be detached from it.\n'''
             '''If the right-click is on a Nexus, the whole Line will be deleted'''),
            '''Congratulations, you've become an Equilibrium Graphs Master!''']

    positions = [{'center_x': .5, 'y': .6},
                 {'right': .98, 'top': .95},
                 {'right': .98, 'top': .95},
                 {'right': .98, 'top': .95},
                 {'right': .98, 'top': .95},  #Canvas
                 {'x': .05, 'y': .05},
                 {'x': .05, 'y': .05},
                 {'x': .05, 'y': .05},
                 {'x': .05, 'y': .05},
                 {'x': .05, 'y': .05},
                 {'right': .85, 'top': .93},  #Side panel
                 {'right': .85, 'top': .93},
                 {'right': .85, 'top': .86},
                 {'x': .05, 'y': .05},  #Canvas again
                 {'x': .05, 'y': .05},
                 {'x': .05, 'y': .05},
                 {'x': .05, 'y': .05},
                 {'right': .85, 'y': .3},  #Lines
                 {'x': .05, 'y': .05},
                 {'x': .05, 'y': .05},
                 {'x': .05, 'y': .05},
                 {'x': .05, 'y': .05}]

    arrows = ['bottom_mid',
              'top_right',
              'top_right',
              'top_right',
              'top_right',  #Canvas
              'top_right',
              'top_right',
              'top_right',
              'top_right',
              'top_right',
              'right_mid',  #Side panel
              'right_mid',
              'right_mid',
              'top_right',  #Canvas again
              'top_right',
              'top_right',
              'top_right',
              'right_mid',  #Lines
              'top_right',
              'top_right',
              'top_right',
              'top_right']

    def __init__(self, end_callback=None, **kwargs):
        self.step = 0
        self.end_callback = end_callback
        super(Tutorial, self).__init__(**kwargs)
        self.ids.button.text = self.msgs[self.step]
        self.pos_hint = self.positions[self.step]
        self.arrow_pos = self.arrows[self.step]

    def next_step(self):
        self.step += 1
        if self.step >= len(self.msgs):
            self.end()
        else:
            self.ids.button.text = self.msgs[self.step]
            self.pos_hint = self.positions[self.step]
            self.arrow_pos = self.arrows[self.step]

    def end(self):
        if self.end_callback is not None:
            self.end_callback()
        self.parent.remove_widget(self)

    def on_release(self):
        self.next_step()
