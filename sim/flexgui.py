#!/usr/bin/env python

# This class provides the GUI wrapper frame
# for visualizing what is going on in the turn
# taking mechanism. It's pretty flexible and
# could be used for other purposes.
#

import kivy

kivy.require('1.0.7')

from kivy.app import App

from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

import time, threading


def label_set_val(instance, value, toSet):  # , toSet=None, theslider=None):
    """
    Callback for the labels
    """
    toSet.value = int(value)


class FlexGui(App):
    def build(self):
        """
        Creates the layout of the app itself.
        """
        self.title = "Turntaking Sim"

        # Create a grid layout
        myLayout = GridLayout(rows=1, cols=2, rows_minimum={0: 500}, cols_minimum={0: 150, 1: 500})
        # Create a stack layout on the left
        self.box = BoxLayout(orientation='vertical', padding=10)
        self.titleLabel = Label(halign="left", size_hint=(1.0, 1.0),
                                text='[b][color=ff3333]Turn taking features:[/color][/b]', markup=True,
                                valign="top")
        self.titleLabel.bind(size=self.titleLabel.setter('text_size'))
        self.box.add_widget(self.titleLabel)

        # a map of widgets you can access later
        self.widget_map = {}
        myLayout.add_widget(self.box)

        # You can replace TT with a simple hello button
        # self.tt_viewer = Button("Hello")
        myLayout.add_widget(self.tt_viewer)

        return myLayout

    def print_line(self, key, value):
        """
        Print a line in the console

        """

        if self.widget_map is None:
            return

        if key not in self.widget_map.keys():
            newText = key + ": " + value
            lbl = Label(halign="left",
                        size_hint=(1.0, 1.0),
                        valign="top",
                        text=newText)
            lbl.bind(size=lbl.setter('text_size'))
            self.widget_map[key] = lbl
            self.box.add_widget(lbl)
        else:
            newText = key + ": " + value
            lbl = self.widget_map[key]
            lbl.text = newText

    def create_slider_int(self, name, minV, maxV, defaultVal=0):
        """
        Creates a slider vizualizer
        """
        if self.widget_map is None:
            return

        if name not in self.widget_map.keys():
            newText = name + ":"
            boxlayout = BoxLayout(orientation='horizontal', padding=0, halign='left')
            lbl = Label(halign="left",
                        size_hint=(1.0, 1.0),
                        valign="top",
                        text=newText)
            lbl.bind(size=lbl.setter('text_size'))

            # I can't believe this works. (NBD)
            valOut = lambda: None
            valOut.value = int(defaultVal)

            numslider = None
            numslider = Slider(min=minV, max=maxV, value=defaultVal)
            numslider.bind(value=lambda x, y: label_set_val(x, y, valOut))
            boxlayout.add_widget(lbl)
            boxlayout.add_widget(numslider)

            self.widget_map[name] = valOut
            self.box.add_widget(boxlayout)
            return valOut
        return None

    def updateTT(self, tt_module):
        """
        Update the turn taking viewer
        """
        obsrs = list(tt_module.observations)
        obsrs[9] = min(1500, obsrs[9]) / 1500

        self.tt_viewer.update(obsrs)


# Simple test to make sure just this flexible GUI works.
if __name__ == "__main__":
    gui = FlexGui()


    def addAbutton():
        time.sleep(1.0)
        print("Adding..")
        gui.print_line("Test", "Test Value")
        time.sleep(1.0)
        print("Changing..")
        gui.print_line("Test", "Test Value 2")


    threading.Thread(target=addAbutton).start()
    gui.run()
