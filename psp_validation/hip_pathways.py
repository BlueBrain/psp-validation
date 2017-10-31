#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Repository for pathway queries - modified by Andras for the hippocampal circuit
Eilif's version used different querying with the possibility of boudled names (like inh_other, which included 5 different cells)
but the hippocampal validation is updated by Giuseppe's pair selection (look at bbputils) -> no need for that kind of (slow) queries
articles about pathways/connections are hosted here: goo.gl/kdUcmu, last update: 12.2016
"""


class Pathway(object):
    """Class holding the queries necessary to obtain pre- and \ post-synaptic cells (this was necassary for the prev. version, but the structure is kept here too)"""

    def __init__(self, presynaptic_cell_query, postsynaptic_cell_query):
        self.presynaptic_cell_query = presynaptic_cell_query
        self.postsynaptic_cell_query = postsynaptic_cell_query

    def __eq__(self, rhs):
        attrs = self.__dict__.keys()
        for attr in attrs:
            if self.__getattribute__(attr) != rhs.__getattribute__(attr):
                return False
        return True

    def __str__(self):
        return "pre: %s -> post: %s"%(self.presynaptic_cell_query, self.postsynaptic_cell_query)

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

# General
EXC = 'MType.synapse_class=="EXC"'
INH = 'MType.synapse_class=="INH"'

# Specific (all unique cell type) check with: c = bluepy.Circuit(circuit_path); available_targets = c.targets.available_targets()
SLM_PPA = 'MType.name=="SLM_PPA"'
SO_BP = 'MType.name=="SO_BP"'
SO_BS = 'MType.name=="SO_BS"'
SO_OLM = 'MType.name=="SO_OLM"'
SO_Tri = 'MType.name=="SO_Tri"'
SP_AA = 'MType.name=="SP_AA"'
SP_BS = 'MType.name=="SP_BS"'
SP_CCKBC = 'MType.name=="SP_CCKBC"'
SP_Ivy = 'MType.name=="SP_Ivy"'
SP_PC = 'MType.name=="SP_PC"'
SP_PVBC = 'MType.name=="SP_PVBC"'
SR_IS1 = 'MType.name=="SR_IS1"'
SR_SCA = 'MType.name=="SR_SCA"'

cell_names = ["SLM_PPA", "SO_BP", "SO_BS", "SO_OLM", "SO_Tri", "SP_AA", "SP_BS", "SP_CCKBC", "SP_Ivy", "SP_PC", "SP_PVBC", "SR_IS1", "SR_SCA"]
cell_types_bp = [SLM_PPA, SO_BP, SO_BS, SO_OLM, SO_Tri, SP_AA, SP_BS, SP_CCKBC, SP_Ivy, SP_PC, SP_PVBC, SR_IS1, SR_SCA]

# allow all to all connections (insted of listing them one-by-one and create groups)
_pathways = dict()
for pre_name, pre_bp in zip(cell_names, cell_types_bp):    
    if pre_name != "SP_AA":  # only axoaxonic cells are handeled differently
        phways = {}
        for post_name, post_bp in zip(cell_names, cell_types_bp):
            key = "%s-%s"%(pre_name, post_name)
            phways[key] = Pathway(pre_bp, post_bp)
        _pathways.update(phways)
    else:
        _pathways.update({"SP_AA-SP_PC":Pathway(SP_AA, SP_PC)})
        

def get_pathway(label) :
    """Return a pathway for a given label"""
    return _pathways[label]

