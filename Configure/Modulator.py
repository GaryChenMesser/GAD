from __future__ import print_function, division, absolute_import
# from util import *
# from mod_util import *
from .mod_util import Attr
class Modulator(object):
    """ * name
        * start
        * profile
        * generator
    """
    def __init__(self, **desc):
        self.desc = desc

    def __getitem__(self, name):
        return self.desc[name]

    def __str__(self):
        return str( Attr(**self.desc) )

    @property
    def profile(self): return self.desc['profile']
    @property
    def start(self):
        # if isinstance(self.desc['start'], str):
            # return eval( self.desc['start'] )
        return self.desc['start']

from .Behaviour import DTMCBehaviour, CTMCBehaviour
class MarkovModulator(Modulator):
    """

    Parameters:
        name : str
            name of modular. now it is useless
        start : float
            start time
        profile : tuple of tuple
            profile
        generator_states : a list of generator names
            representing the states
        node_para : dict
            * type : {'DTMC', 'CTMC'}
            * P : nxn matrix
                Pij is transition probability from i to j when type=='DTMC',
                Pij is rate of possion process that transition i to j will
                happen
            * interval : float
                mean of interval time. useful for only 'DTMC'

    """
    def __init__(self, name, start, profile, generator_states, node_para):
        Modulator.__init__(self, name=name, start=start, profile=profile)
        self.name = name
        self.states = generator_states
        # self.start = start
        # self.profile = profile
        self.mod_list = []
        type_ = node_para['type']
        P = node_para['P']
        if type_ == 'DTMC':
            it = node_para['interval']
            self.behaviour = DTMCBehaviour(P, generator_states, it)
        elif type_ == 'CTMC':
            self.behaviour = CTMCBehaviour(P, generator_states)
        else:
            raise Exception("unknown Behaviour Type")

        self.sync()

    def sync(self):
        self.behaviour.behave_with_profile(self.start, self.profile, self.stage)

    def __str__(self):
        return ' '.join([str(mod) for mod in self.mod_list])

    def stage(self, r_start, r_end, state):
        """for one markov stage"""
        mod = Modulator(
                name=self.name,
                start=r_start,
                profile=( (r_end-r_start,), (1,) ) ,
                generator=state,
                )
        self.mod_list.append(mod)

from .Behaviour import MVBehaviour
class MVModulator(Modulator, MVBehaviour):
    """
    Modulator defines the behaviour of generator within a range of time.
    implement the stage function.
    joint_dist should be numpy array
    """
    def __init__(self, joint_dist, interval, generator_states, **desc):
        Modulator.__init__(self, **desc)
        MVBehaviour.__init__(self, joint_dist, interval, generator_states)
        self.mod_list = []
        self.behave_with_profile(self.start, self.profile)

    def stage(self):
        """for one stage"""
        r_start = self.run_para['r_start']
        r_end = self.run_para['r_end']
        for i in xrange(self.srv_num): # for each destination
            gen = self.states[i][self.cs[i]]
            if not gen:
                continue
            mod = Modulator(
                    name=self.desc['name'],
                    start=r_start,
                    profile=( (r_end-r_start,), (1,) ) ,
                    generator=gen,
                    )
            self.mod_list.append(mod)
