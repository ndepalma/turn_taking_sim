#!/usr/bin/env python
#
# Render the simulator state to the screen
#

import kivy

from sim.util import timems

kivy.require('1.0.7')

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout

from kivy.core.window import Window
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Mesh, PushMatrix, PopMatrix
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.graphics import Rotate, Line
from kivy.graphics.instructions import InstructionGroup

import time, math, threading


class PyGameVis(FloatLayout):
    """
    This is the class that actually renders the state of the simulator to the Kivy canvas
    """
    def __init__(self, x, timelineheight, points=[], loop=False, *args, **kwargs):
        super(PyGameVis, self).__init__(*args, **kwargs)
        self.loop = loop
        self.center = (250, 500 - 150)

        self.x = x

        self.gestureGroup = InstructionGroup()
        self.gestureGroup.add(Color(0, 0, 1, 0.2))

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        self.timelineGroup = InstructionGroup()
        self.textGroup = InstructionGroup()
        with self.canvas:
            # Add a red color
            Color(0.5, 0, 0)

            # Add a rectangle
            Ellipse(pos=(125 + self.x + self.center[0], self.center[1]), size=(5, 5))

        self.canvas.add(self.gestureGroup)
        self.canvas.add(self.timelineGroup)
        self.canvas.add(self.textGroup)

        self.on_keys = None

        self.timelineheight = timelineheight

    def _keyboard_closed(self):
        """
        Remove keyboard controls
        """
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """
        What was pressed
        """
        print("Key down")
        self.on_keys()
        return True

    def set_keyboard_handler(self, on_keysI):
        """
        Set the external function callback to be called when a key is pressed
        """
        self.on_keys = on_keysI

    def addChar(self, pos_new, color_new):
        """
        Add a new character and pick a color for it
        """
        col_out = lambda: None

        # Gesturing hooks
        col_out.color = Color(rgb=(0, 100.0 / 255.0, 100.0 / 255.0))
        self.gestureGroup.add(col_out.color)
        self.gestureGroup.add(Ellipse(pos=(self.x + pos_new[0] - 10, pos_new[1] - 10), size=(20, 20)))
        ##############
        (px, py) = pos_new
        px = px + self.x
        thetaRot = 0
        tipdist = 18
        backdist = 15
        # compute dir of the triangle tip
        ##-------------------
        cx = math.cos(thetaRot)
        cy = -math.sin(thetaRot)

        tip = [px + cx * tipdist, py + cy * tipdist, 0, 0]

        # compute the other two positions opposite the center point
        ##-------------------
        backlefttheta = thetaRot + math.pi + math.radians(20)
        cx = math.cos(backlefttheta)
        cy = math.sin(backlefttheta)

        backleft = [px + cx * backdist, py - cy * backdist, 0, 0]
        ##-------------------
        backrighttheta = thetaRot + math.pi - math.radians(20)
        cx = math.cos(backrighttheta)
        cy = math.sin(backrighttheta)

        backright = [px + cx * backdist, py - cy * backdist, 0, 0]
        ##-------------------

        vertices = tip + backleft + backright
        indices = [0, 1, 2]

        #################
        # Actual character
        col_out.rotate = Rotate(angle=0., origin=(self.pos[0] + pos_new[0], self.pos[1] + pos_new[1]))
        self.gestureGroup.add(Color(rgb=color_new))
        self.gestureGroup.add(PushMatrix())
        self.gestureGroup.add(col_out.rotate)
        self.gestureGroup.add(Mesh(vertices=vertices, indices=indices, mode='triangles'))
        self.gestureGroup.add(PopMatrix())

        return col_out

    def blankScreen(self):
        """
        What happens when a screen is refreshed
        """
        pass

    def drawJib(self, utterance):
        """
        Draw some gibberish utterance.
        """
        mylabel = CoreLabel(text=utterance, font_name=u'wasy10', font_size=24, color=(1, 1, 1, 1))
        # Force refresh to compute things and generate the texture
        mylabel.refresh()
        # Get the texture and the texture size
        self.texture = mylabel.texture
        # self.textsurface = self.jibfont.render(utterance, True, (255, 255, 255))
        self.textGroup.clear()

    def putJib(self, center):
        """
        Puts the jibberish at a specific place
        """
        (x, y) = center
        texture_size = list(self.texture.size)
        # Draw the texture on any widget canvas
        self.textsurface = Rectangle(texture=self.texture, size=texture_size, pos=(self.pos[0] + x,
                                                                                   self.pos[1] + 480 - y))
        self.textGroup.add(self.textsurface)
        pass

    def update(self):
        """
        Update the canvas
        """
        self.canvas.ask_update()
        pass

    def evalSpaceBar(self, on_spacebar, on_quit):
        """
        On spacebar
        """
        pass

    def drawChar(self, center, pos, drawOuterCircle, thetaRot, color, thechar):
        """
        Draw a character looking in a specific direction with a certain color
        """
        if drawOuterCircle:
            thechar.color.r = 0
            thechar.color.g = 100. / 255.
            thechar.color.b = 0
        else:
            thechar.color.r = 0
            thechar.color.g = 0
            thechar.color.b = 0

        thechar.rotate.angle = -math.degrees(thetaRot)


class MyPaintApp(App):
    """
    Wrapper for Kivy
    """
    def build(self):
        self.title = "Turntaking Sim"
        return self.mybuild


class TimelineViz:
    """
    Timeline widget
    """

    def __init__(self, x, height, instruc_group):
        self.height = height
        self.width = 500

        self.feature_xtracters = [["Person 1:", lambda x: x[3][0] == 0 and x[0][1]],
                                  ["Person 2:", lambda x: x[3][0] == 1 and x[0][1]],
                                  ["Person 3:", lambda x: x[3][0] == 2 and x[0][1]],
                                  ["Person 4:", lambda x: x[3][0] == 3 and x[0][1]],
                                  ["Robot:", lambda x: x[3][0] == -1]]

        self.timelines = None
        self.t_init = timems()
        self.t_last = self.t_init

        self.instructs = instruc_group
        self.x = x

    def update(self, features):
        """
        On update
        """
        if self.timelines == None:
            self.timelines = [[]] * len(self.feature_xtracters)

        t_now = timems()
        if t_now - self.t_init > 2000:
            t_begin = t_now - 2000
            t_middle = t_now
            t_end = t_now + 2000
        else:
            t_begin = self.t_init
            t_middle = t_begin + 2000
            t_end = t_begin + 4000

        # print("Features: " + str(features))
        now_state = list(map(lambda fn: fn[1](features), self.feature_xtracters))
        # print("now state: " + str(now_state))

        for row in range(len(self.timelines)):
            numlinesinrow = len(self.timelines[row])
            # for that row, determine if start, extend, or end
            if now_state[row]:
                # continue or start
                if numlinesinrow > 0:
                    # something here.. check if we should continue it or stop it
                    if len(self.timelines[row][numlinesinrow - 1]) == 3:
                        # start a new one - the last one had an end marker
                        newlines = list(self.timelines[row])
                        newlines.append([t_now, t_now])
                        self.timelines[row] = newlines
                    else:
                        self.timelines[row][numlinesinrow - 1][1] = t_now
                else:
                    # nothing on this line at all. just start a new line
                    newlines = list(self.timelines[row])
                    newlines.append([t_now, t_now])
                    self.timelines[row] = newlines
            else:
                # end
                if numlinesinrow > 0 and len(self.timelines[row][numlinesinrow - 1]) == 2:
                    # end it
                    (self.timelines[row][numlinesinrow - 1]).append(None)

        # prune the lines
        self.instructs.clear()
        self.instructs.add(Color(1., 1., 1.))
        self.instructs.add(Rectangle(size=(self.width, self.height), pos=(self.x, 0)))

        self.render_timegrid(t_begin, t_middle, t_end)

    def get_text_texture(self, textO, posO):
        """
        Creates a texture for the text at a specific position
        """
        mylabel = CoreLabel(text=textO, font_size=12, color=(0, 0, 0, 1))
        # Force refresh to compute things and generate the texture
        mylabel.refresh()
        # Get the texture and the texture size
        texture = mylabel.texture
        texture_size = list(texture.size)
        # Draw the texture on any widget canvas
        return Rectangle(texture=texture, size=texture_size, pos=posO)

    def render_timegrid(self, tbegin, tmid, tend):
        """
        Renders the grid to the canvas
        """
        tb_act = (tbegin - self.t_init) / 1000.0
        tm_act = (tmid - self.t_init) / 1000.0
        te_act = (tend - self.t_init) / 1000.0

        # Render the text
        y = 5
        x = int(0)
        textO = str("{0:.1f}".format(tb_act))
        self.instructs.add(self.get_text_texture(textO, (self.x + x, y)))

        x = (self.width / 2) - 8
        textO = str("{0:.1f}".format(tm_act))
        self.instructs.add(self.get_text_texture(textO, (self.x + x, y)))

        x = self.width - 17
        textO = str("{0:.1f}".format(te_act))
        self.instructs.add(self.get_text_texture(textO, (self.x + x, y)))

        # Render the line delineating the text at the bottom
        self.instructs.add(Color(200. / 255., 200. / 255., 200. / 255.))
        self.instructs.add(Line(points=[self.x, 20, self.x + self.width, 20], width=1))

        self.instructs.add(Color(210. / 255., 210. / 255., 210. / 255.))
        # Mark the seconds lines
        pt = int(tb_act)
        for _ in range(5):
            if tb_act < pt < te_act:
                npt = (pt - tb_act) / 4.0
                x = npt * self.width
                self.instructs.add(Line(points=[self.x + x, self.height, self.x + x, 20], width=1))
            pt = pt + 1

        timelinecolor = (0, 200, 200)
        y = self.height - 12
        # Actually draw the lines
        for row in range(len(self.timelines)):
            lines = self.timelines[row]
            linestokeep = list([])
            self.instructs.add(Color(rgb=timelinecolor))

            for line in lines:
                # check if the line is in bounds
                line_start = line[0]
                line_end = line[1]

                if (tbegin < line_start < tend) or (tbegin < line_end < tend):
                    # don't cull the line, it's in bounds
                    linestokeep.append(line)
                    line_start = max(line_start, tbegin) - tbegin
                    line_end = min(line_end, tend) - tbegin

                    # normalize them
                    line_begin_norm = line_start / 4000.0
                    line_end_norm = line_end / 4000.0

                    # now fit them to the width
                    x_start = line_begin_norm * self.width
                    x_end = line_end_norm * self.width
                    self.instructs.add(Line(points=[self.x + x_start, y, self.x + x_end, y], width=1))

            #            self.timelines[row] = linestokeep
            label = str(self.feature_xtracters[row][0])

            self.instructs.add(self.get_text_texture(label, (self.x, y)))
            y = y - 13


def wrapVis(visualizer, timelineheight):
    """
    Wrap the visualizer, create the paint canvas and return the new instance
    """
    theapp = MyPaintApp()
    theapp.mybuild = visualizer
    Window.size = (500, 300 + timelineheight)
    return theapp


if __name__ == '__main__':
    timelineheight = 200
    app = wrapVis(thewidget, timelineheight)

    tlgr = TimelineViz(timelineheight, thewidget.timelineGroup)


    def funtest():
        time.sleep(1)
        print("adding")
        thewidget.addChar((100, 400), (0, 100.0 / 255.0, 0))
        print("adding2")
        col = thewidget.addChar((300, 400), (0, 100.0 / 255.0, 100.0 / 255.0))
        time.sleep(1)
        print("chg1")
        col.color.r = 0.0
        col.color.g = 0.0
        col.color.b = 0.0
        print("ask update")
        # thewidget.canvas.ask_update()
        print("Exit")
        for _ in range(100):
            time.sleep(0.1)
            tlgr.update(None)


    thr = threading.Thread(target=funtest)
    thr.start()
    app.run()
