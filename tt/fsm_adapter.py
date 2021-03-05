#!/usr/bin/env python
#
# Interface to implement for any FSM
#

f_voice_activity = 0
f_action_queued = 1
f_utterance_complete = 2
f_other_lookat = 3
f_other_presenting = 4
f_who_talking = 5
f_running_action = 6
f_wants_turn = 7
f_other_accepts = 8
timesincelastactivity = 9


class Adapter:
    def transform_features(self, features_in):
        #overload for the transform
        return features_in
    #optional functions
    def startup(self):
        pass
    def shutdown(self):
        pass
    #get the current features
    def getFeatures(self):
        return None
