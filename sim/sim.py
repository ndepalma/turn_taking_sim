#!/usr/bin/env python
#
# Backend for the simulator
#

import math
import time
import random

from sim.sim_vis import TimelineViz, PyGameVis

from sim.flexgui import FlexGui
import threading

import tt.fsm_adapter
from sim.util import timems


class ModelInterface:
    """
    Abstract class
    """

    def queue_action(self):
        pass


class Character:
    """
    A character that can speak and be visualized
    """

    def __init__(self, center, theta_from_center, dist_from_center, id, visualizer):
        self.conv_pos = [theta_from_center, dist_from_center]

        px = self.conv_pos[1] * math.cos(self.conv_pos[0])
        py = self.conv_pos[1] * -math.sin(self.conv_pos[0])

        px = int(px + center[0])
        py = int(py + center[1])

        self.pos = (px, 500 - py)
        self.theta = theta_from_center
        self.desired_theta = 0
        self.mycolor = (255, 0, 0)
        self.isnonverbal = True  # random.randint(0,1) == 1
        self.isGesturing = False
        self.id = id
        self.visualizer = visualizer
        self.char = None

    def drawChar(self, center):
        """
        Draw the character on the pygame board
        """
        if self.char is None:
            self.char = self.visualizer.addChar(self.pos, self.mycolor)
        self.visualizer.drawChar(center, self.pos, self.isGesturing, self.theta, self.mycolor, self.char)

    def update(self):
        """
        Update function, all the work happens here
        """
        # map to 0-360
        x_z3 = (self.theta + (2 * math.pi)) % (2 * math.pi)
        y_z3 = (self.desired_theta + (2 * math.pi)) % (2 * math.pi)

        if abs(y_z3 - x_z3) < math.pi:
            # go ccw (compute the difference in 0-360 and add to old space)
            self.theta = (y_z3 - x_z3) / 4 + self.theta
        else:
            # go cw (compute difference in -180-180 space )
            self.theta = (self.desired_theta - self.theta) / 4 + self.theta

    def look_at(self, angle):
        """
        Make the character look in some angle
        """
        self.desired_theta = angle

    def getPos(self):
        """
        Get the position of the character
        """
        return self.pos

    def try_footing(self):
        """
        Try to grab the floor by randomly gesturing
        """
        self.isGesturing = random.randint(0, 1) > 0 if self.isnonverbal else False

    def reset_footing(self, idwhogot):
        """
        Change who is talking
        """
        self.isGesturing = self.isGesturing if idwhogot == self.id else False


class Robot(Character):
    """
    The machine in the game
    """

    def __init__(self, center, theta_from_center, dist_from_center, visualizer):
        Character.__init__(self, center, theta_from_center, dist_from_center, -1, visualizer)
        self.mycolor = (100. / 255., 100. / 255., 100. / 255.)
        self.queuedAction = False
        self.my_turn = False

    def try_footing(self):
        """
        Try to take an action if I have one queued up
        """
        self.my_turn = False
        if self.queuedAction:
            self.isGesturing = True

    def reset_footing(self, idwhogot):
        """
        Try to take an action if I have one queued up
        """
        self.isGesturing = self.isGesturing if idwhogot == self.id else False
        if self.isGesturing:
            # start talking
            self.my_turn = True
        else:
            self.my_turn = False


class UniformCirclePlacer:
    def __init__(self):
        self.slots = []

    def getNextAngle(self):
        """
        Places the characters in a 'conversational circle'. This is called "formation"
        """
        mindist = math.radians(38)
        anglefromcenter = random.uniform(-math.pi, math.pi)

        while len(list(filter(lambda x: abs(x - anglefromcenter) < mindist, self.slots))) > 0:
            anglefromcenter = random.uniform(-math.pi, math.pi)

        self.slots.append(anglefromcenter)
        return anglefromcenter


class Scene:
    """
    Characters and robots in a conversational circle. Handles top level simualtion management
    """

    def __init__(self, npeople, visualizer):
        self.people = []
        self.center = (250, 150)
        self.bubbler = UtteranceBubbler(visualizer, (120, 50), None)
        self.turnstate = TurnState(npeople, self.bubbler)

        slots = UniformCirclePlacer()
        for i in range(npeople):
            anglefromcenter = slots.getNextAngle()
            char = Character(self.center, anglefromcenter, 50, i, visualizer)
            self.people.append(char)

        anglefromcenter = slots.getNextAngle()
        self.robot = Robot(self.center, anglefromcenter, 50, visualizer)

        self.gazestate = GazeState(npeople, self.center, self.people)
        self.gazestate.setGazeState(self.turnstate, self.robot)

        self.tryingfooting = False

    def updateVis(self, stateIn):
        """
        Draw the scene
        """
        turnChange = self.turnstate.update(self.people, self.robot)
        if turnChange is not None:
            if turnChange:
                map(lambda char: char.reset_footing(self.turnstate.whospeaking), self.people)
                self.robot.reset_footing(self.turnstate.whospeaking)
                self.tryingfooting = not self.tryingfooting
                self.gazestate.setGazeState(self.turnstate, self.robot)
            elif not self.bubbler.isSpeaking() and not self.tryingfooting:
                print("Trying to foot")
                self.tryingfooting = not self.tryingfooting
                map(lambda char: char.try_footing(), self.people)
                self.robot.try_footing()
        else:
            # Let silence lay
            print("Trying to foot again")
            map(lambda char: char.try_footing(), self.people)
            self.robot.try_footing()

        for i in range(len(self.people)):
            person = self.people[i]
            person.look_at(self.gazestate.lookat[i])
            person.update()
            person.drawChar(self.center)

        self.robot.update()
        self.robot.drawChar(self.center)

        if turnChange:
            self.bubbler.randomUtterance(None)

        self.bubbler.drawUtterance()

    def makeRobotLookAtPerson(self, whichPerson):
        """
        Exactly as it seems
        """
        angle = computeTheta(self.robot.getPos(), self.gazestate.people[whichPerson].getPos())
        self.robot.look_at(angle)

    def getFeatures(self):
        """
        See who is gesturing in the conversational circle. These features are used as input to the robot's decision making
        """
        return [person.isGesturing for person in self.people]


def computeTheta(myPos, lookAtPos):
    """
    Computes the theta to direct the gaze at the target
    """
    dx = lookAtPos[0] - myPos[0]
    dy = lookAtPos[1] - myPos[1]
    ang = -math.atan2(dy, dx)
    return ang


class GazeState:
    """
    This is a simple class that can change the direction of the gaze based on who's talking and who they want to talk to
    """

    def __init__(self, npeople, center, people):
        self.npeople = npeople
        self.lookat = [0] * npeople
        self.centerPos = center

        for i in range(npeople):
            self.lookat[i] = None
        self.people = people

    def setGazeState(self, turnstate, robot):
        """
        Meat of the gaze decision
        """
        whoIndex = turnstate.whospeaking
        print("Who's turn: " + str(whoIndex))
        whopos = self.people[whoIndex].getPos()
        for i in range(self.npeople):
            l = whopos
            if whoIndex == -1:
                l = robot.getPos()
            elif i == whoIndex:
                if self.lookat[i] is not None:
                    continue
                else:
                    if self.npeople == 1:
                        l = robot.getPos()
                    else:
                        somei = (whoIndex + 1) % self.npeople
                        l = self.people[somei].getPos()
            self.lookat[i] = computeTheta(self.people[i].getPos(), l)

    def __compute_three_point_features(self, robot):
        """
        gets the gaze features by extracting the gaze targets as ordinals of people
        """
        features_out = []
        for i in range(len(self.people)):
            person = self.people[i]
            th = computeTheta(person.getPos(), robot.getPos())
            dtheta = th - self.lookat[i]

            x_z3 = (self.lookat[i] + (2 * math.pi)) % (2 * math.pi)
            y_z3 = (th + (2 * math.pi)) % (2 * math.pi)

            if abs(dtheta) < math.radians(30):
                if abs(y_z3 - x_z3) < math.pi:
                    dtheta = x_z3 - y_z3
                    if dtheta < -math.radians(30):
                        features_out.append(-1)
                    elif dtheta > math.radians(30):
                        features_out.append(1)
                    else:
                        features_out.append(0)
                else:
                    features_out.append(-2)
            else:
                features_out.append(-2)

            # if i == 0:
            #     print("th: " + str(math.degrees(th)))

            #     print("x: " + str(math.degrees(x_z3)))
            #     print("y: " + str(math.degrees(y_z3)))

            #     print("Feature for person zero and robot: " + str(dtheta))
        return features_out

    def getFeatures(self, robot):
        """
        External function that is called
        """
        return self.__compute_three_point_features(robot)

    def getPositions(self):
        return [p.getPos() for p in self.people]


class TurnState:
    """
    Determins who gets the next turn. This is mostly chosen randomly
    """

    def __init__(self, npeople, utterer):
        self.whospeaking = -1
        self.cadence = 500
        self.lastStamp = -1
        self.npeople = npeople
        self.speakerbox = utterer
        self.whospeaking = 0
        self.cadence = random.randint(-200, 200) + 500

    def __pickNext(self, peoplefooting, robotfooting):
        """
        This picks who is next to speak. Sadly, it's not really about anything more than random.
        """
        possibilities = list(filter(lambda x: x.isGesturing, peoplefooting))
        if robotfooting.isGesturing:
            possibilities.append(robotfooting)
        if len(possibilities) == 0:
            self.whospeaking = -2
        else:
            self.whospeaking = random.randint(0, len(possibilities) - 1)
            self.whospeaking = possibilities[self.whospeaking].id
            self.cadence = random.randint(-200, 200) + 500
        return self.whospeaking

    def update(self, footingpeople, footingrobot):
        """
        Meat of the turn state update
        """
        if self.lastStamp == -1:
            self.lastStamp = timems()
        if not self.speakerbox.isSpeaking() and timems() - self.lastStamp > self.cadence:
            # see who's turn it is
            whonext = self.__pickNext(footingpeople, footingrobot)
            if whonext == -2:
                return None
            print("Person " + str(self.whospeaking) + "'s turn.")
            return True
        elif self.speakerbox.isSpeaking():
            self.lastStamp = timems()
        return False

    def getFeatures(self):
        """
        Just who is speaking
        """
        is_speaking = self.speakerbox.isSpeaking()
        return [self.whospeaking]


class UtteranceBubbler:
    """
    Displays garbly utterance. Researchers have found what is spoken matters to who takes the next turn.
    We don't take these semantics into account very deeply here. We just return whether or not a pronoun was used.
    """

    def __init__(self, visualizer, center, distance):
        self.center = center
        self.distance = distance
        self.visualizer = visualizer
        self.forhowlong = 0
        self.randomUtterance(None)

    def renderUtterance(self, utterance, fromAngle):
        """
        Render the text
        """
        self.visualizer.drawJib(utterance)

    def isSpeaking(self):
        """
        Determines how long it takes to say something
        """
        return timems() - self.lastStamp < self.forhowlong

    def randomUtterance(self, fromAngle):
        """
        Synthesizes a random utterance and make it come from a specific person
        """
        numwords = 2  # random.randint(1,4)
        self.forhowlong = random.randint(1, 10) * 1000
        phrase = ""
        self.lastStamp = timems()
        for _ in range(numwords):
            wordlen = random.randint(1, 3)
            wrd = ''
            for _ in range(wordlen):
                nextChar = chr(ord('A') + random.randint(0, 25)) + 'A'
                wrd = wrd + nextChar
            phrase = phrase + wrd + " "

        # 1 in 10 chance of using pronoun
        self.includespronoun = 1 if random.random() < 0.3 else 0
        self.renderUtterance(phrase, fromAngle)

    def drawUtterance(self):
        """
        Draw the utterance in the visualizer
        """
        if self.isSpeaking():
            self.visualizer.putJib(self.center)

    def getFeatures(self):
        """
        Get the features that'll be used for the state machine
        """
        return [self.includespronoun, self.isSpeaking()]


class Simulator(threading.Thread):
    """
    Encapsulate the whole simulator and model and run the sim.
    """

    def __init__(self, model, npeople):
        # type: (ModelInterface) -> None
        threading.Thread.__init__(self)

        timelineheight = 200
        tlx = 300

        self.visualizer = PyGameVis(150, timelineheight)

        # kivy
        self.app = FlexGui()  # wrapVis(self.visualizer, timelineheight)
        self.app.tt_viewer = self.visualizer

        self.circle = Scene(npeople, self.visualizer)
        self.timeline = TimelineViz(tlx, timelineheight, self.visualizer.timelineGroup)

        self.model = model

        self.running = True

    def getFeatures(self):
        """
        Aggregate all of the features
        """
        gazefeatures = self.circle.gazestate.getFeatures(self.circle.robot)
        utterancefeatures = self.circle.bubbler.getFeatures()
        turnfeatures = self.circle.turnstate.getFeatures()
        posfeatures = self.circle.gazestate.getPositions()
        scenefeatures = self.circle.getFeatures()

        return [utterancefeatures, gazefeatures, posfeatures, turnfeatures, scenefeatures]

    def stopRunning(self):
        """
        Stop running the simulator
        """
        self.running = False

    def quit(self):
        """
        Call this function to stop the simulator
        """
        self.app.stop()

    def startVis(self):
        """
        Starts the sim and the threads
        """
        # this blocks until the user closes the window
        self.app.run()
        self.running = False

    def run(self):
        """
        Run loop
        """
        time.sleep(0.5)
        while self.running:
            dx = 0
            dz = 0

            self.visualizer.blankScreen()
            self.circle.updateVis(self.visualizer)
            self.visualizer.canvas.ask_update()

            features = self.getFeatures()
            # self.timeline.update(self.visualizer, self.circle, features)
            self.timeline.update(features)  # self.visualizer, self.circle, features)
            time.sleep(0.05)

            self.visualizer.set_keyboard_handler(self.model.queue_action)
            # print("Features: " + str(features))
            # self.visualizer.evalSpaceBar(self.model.queueAction, self.stopRunning)
            self.visualizer.update()

    def vis_features(self, observations, current_state):
        """
        Visualize the features.
        """
        self.app.print_line("Time since voice activity", str(observations[tt.fsm_adapter.f_voice_activity]))
        self.app.print_line("Is action queued?", str(observations[tt.fsm_adapter.f_action_queued]))
        self.app.print_line("Are they done talking?", str(observations[tt.fsm_adapter.f_utterance_complete]))
        self.app.print_line("Is someone looking at me?", str(observations[tt.fsm_adapter.f_other_lookat]))
        self.app.print_line("Is gesturing towards me?", str(observations[tt.fsm_adapter.f_other_presenting]))
        self.app.print_line("Who is talking (index)", str(observations[tt.fsm_adapter.f_who_talking]))
        self.app.print_line("Am I running an action?", str(observations[tt.fsm_adapter.f_running_action]))
        self.app.print_line("Someone wants turn?", str(observations[tt.fsm_adapter.f_wants_turn]))
        self.app.print_line("Are they taking the floor?", str(observations[tt.fsm_adapter.f_other_accepts]))
        self.app.print_line("Time in millis since last turn", str(observations[tt.fsm_adapter.timesincelastactivity]))
        self.app.print_line("Current state", str(current_state.name))
