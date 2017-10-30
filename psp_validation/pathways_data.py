
class PathwayData(object):

    def __init__(self, pre, post, v_holding, psp, syns_per_conn, label):
        for k,v in locals().iteritems():
            if not k == 'self' :
                setattr(self, k, v)

    def __eq__(self, rhs) :
        attrs = self.__dict__.keys()
        for a in attrs :
            if self.__getattribute__(a) != rhs.__getattribute__(a) :
                return False
        return True

    def __str__(self) :
      return 'PathwayData{%s}' % (self.__dict__)

# Neuron group expressions 

# General
EXC = 'MType.synapse_class=="EXC"'
INH = 'MType.synapse_class=="INH"'
MC = 'MType.name.like("L%_MC")'

#Distal Targeting INH
DISTAR_INH = 'Or(MType.name.like("L%_MC"), MType.name.like("L%_BTC"), MType.name.like("L%_DBC"), MType.name.like("L%_BP"))'
BC = 'Or(MType.name.like("L%_NBC"), MType.name.like("L%_LBC"), MType.name.like("L%_SBC"))'
PV_FS = 'Or(MType.name.like("L%_NBC"), MType.name.like("L%_LBC"), MType.name.like("L%_SBC"), MType.name.like("L%_ChC"))'

INH_OTHER = 'And(MType.synapse_class=="INH", Not(%s), Not(%s))' % (PV_FS, DISTAR_INH)


# Specific 
L5_TTPC = 'Or(MType.name=="L5_TTPC1", MType.name=="L5_TTPC2")'
L5_STPC = 'MType.name=="L5_STPC"'
L5_MC = 'MType.name=="L5_MC"'
L5_BC = 'Or(MType.name=="L5_SBC", MType.name=="L5_LBC", MType.name=="L5_NBC")'
L5_PC = 'And(MType.morph_class=="PYR", Neuron.layer==5)'

L2_PC = 'And(MType.name=="L23_PC", Neuron.layer==2)'
L2_BTC = 'And(MType.name=="L23_BTC", Neuron.layer==2)'
L3_PC = 'And(MType.name=="L23_PC", Neuron.layer==3)'
L23_PC = 'MType.name=="L23_PC"'
L23_LBC = 'MType.name=="L23_LBC"'
L23_NBC = 'MType.name=="L23_NBC"'
L23_BC = 'Or(MType.name=="L23_SBC", MType.name=="L23_LBC", MType.name=="L23_NBC")'
L23_NBC_LBC = 'Or(MType.name=="L23_LBC", MType.name=="L23_NBC")'
L23_MC = 'MType.name=="L23_MC"'
L23_BTC = 'MType.name=="L23_BTC"'
L23_DBC = 'MType.name=="L23_DBC"'
L23_BP = 'MType.name=="L23_BP"'
L23_NGC = 'MType.name=="L23_NGC"'
L23_SBC = 'MType.name=="L23_SBC"'
L23_ChC = 'MType.name=="L23_ChC"'

L4_EXC = 'And(MType.synapse_class=="EXC", Neuron.layer==4)'
L4_SS = 'MType.name=="L4_SS"'

L6_TPC_L1 = 'MType.name=="L6_TPC_L1"'


exc_exc_pathways = [
    PathwayData(L5_TTPC, L5_TTPC, -67.0, (1.3, 1.1), (5.5, 1.1), "L5_TTPC-L5_TTPC (Markram 97)"),
    PathwayData(L4_EXC, L4_EXC, -69.0, (1.59, 1.51), (3.4, 1.0), "L4_EXC-L4_EXC (Feldmeyer 04)"),
    PathwayData(L4_SS, L23_PC, -69.0, (0.7, 0.6), (4.5, 0.5), "L4_SS-L23_PC (Feldmeyer 02)"),
    PathwayData(L5_STPC, L5_STPC, -69.0, (0.8, 0.2), (4.0, 0.3), "L5_STPC-L5_STPC (Le Be 06)"),
    PathwayData(L23_PC, L23_PC, -69.0, (1.0, 0.7), None, "L23_PC-L23_PC (?)"),
    # the following pathways were added by nancy from Eilif's script: secondary_pathways_data
    PathwayData(L4_SS, L5_TTPC, -69, (0.6, 0.4), (2.4, 0.9), "L4_SS-L5_TTPC (Feldmeyer 05)")
]
# "L5_TTPC-L5_TTPC (Markram 97)", "L4_EXC-L4_EXC (Feldmeyer 04)", "L4_SS-L23_PC (Feldmeyer 02)",  "L5_STPC-L5_STPC (Le Be 06)", "L23_PC-L23_PC (?)"

exc_inh_pathways = [
    # OK. Scaled, see validation_rescaling_l5pc2mc.log svn r5899, psp amp 0.30mV+-0.19mV
    PathwayData(L5_TTPC, L5_MC, -70.0, (0.28, 0.3), (8.6, 2.1), "L5_TTPC-L5_MC (Silberberg)"),
    # OK, Scaled.  See notes.  RESULT: 'L5 PC-BC (Angulo 99)' psp mean=2.286187, std=2.096072, Nsyns/conn=4.333333
    PathwayData(L5_PC, L5_BC, -72.0, (2.1, 1.3), None, "L5 PC-BC (Angulo 99)"),
    # added by Nancy in exc_inh_pathways
    PathwayData(L4_EXC, L23_LBC, -69.0, (1.2, 1.1), (2.3, 0.8), "L4_EXC-L23_LBC (?)"),
    PathwayData(L4_EXC, L23_NBC, -69.0, (1.2, 1.1), (2.3, 0.8), "L4_EXC-L23_NBC (?)"),
    PathwayData(L4_EXC, L23_MC, -69.0, (1.2, 1.1), (2.3, 0.8), "L4_EXC-L23_MC (?)"),
    #PathwayData(L4_EXC, L23_BTC, -69.0, (1.2, 1.1), (2.3, 0.8), "L4_EXC-L23_BTC (?)"),
    PathwayData(L4_EXC, L23_BP, -69.0, (1.2, 1.1), (2.3, 0.8), "L4_EXC-L23_BP (?)"),
    PathwayData(L4_EXC, L23_NGC, -69.0, (1.2, 1.1), (2.3, 0.8), "L4_EXC-L23_NGC (?)"),
    PathwayData(L4_EXC, L23_SBC, -69.0, (1.2, 1.1), (2.3, 0.8), "L4_EXC-L23_SBC (?)"),
    PathwayData(L4_EXC, L23_ChC, -69.0, (1.2, 1.1), (2.3, 0.8), "L4_EXC-L23_ChC (?)")
]
# "L5_TTPC-L5_MC (Silberberg)", "L5 PC-BC (Angulo 99)"

inh_exc_pathways = [
    # OK, Scaled.  This one have trouble with scaling current, because its close to 
    # threshold for PCs.  Had some manual intervention required.
    #See notes.  0.63311672727272716 +- 0.97149240108010115 mV
    # See 
    PathwayData(L5_MC, L5_TTPC, -57.3, (0.5, 0.4), (12, 3), "L5_MC-L5_TTPC (Silberberg)"),
    # OK, Scaled.  See notes. RESULT: 'L23_LBC-L23_PC (?)' psp mean=0.955161, std=0.728917, Nsyns/conn=15.083333
    PathwayData(L23_LBC, L23_PC, -66.0, (1.21, 1.18), (14.5, 1.7), "L23_LBC-L23_PC (?)"),
    # OK, Scaled. See notes.  RESULT: 'L23_NBC-L23_PC (?)' psp mean=0.950575, std=0.592502, Nsyns/conn=13.833333
    PathwayData(L23_NBC, L23_PC, -66.0, (1.21, 1.18), (15.8, 4.1), "L23_NBC-L23_PC (?)"),
    PathwayData(L23_BC, L23_PC, -66.0, (1.21, 1.18), (14.5, 1.7), "L23_BC-L23_PC (?)"),
    PathwayData(L23_NBC_LBC, L23_PC, -66.0, (1.21, 1.18), (14.5, 1.7), "L23_NBC_LBC-L23_PC (?)")
]

# secondary pathways

# TODO adjust nsyns/conn, data on PSP amp
exc_exc_secondary_pathways = [PathwayData(L6_TPC_L1, L6_TPC_L1, -69.0, (1.2, 0.4), None, "L6_TPC_L1-L6_TPC_L1")]




# "L5_MC-L5_TTPC (Silberberg)", "L23_LBC-L23_PC (?)", "L23_NBC-L23_PC (?)", "L23_BC-L23_PC (?)"

# Predictions

# lumped pathway # PSP data here are unknown
inh_to_all_lumped_pathways = [PathwayData(BC, EXC, -66.0, (1.21, 1.18), (14.5, 1.7), "BC-EXC"),
                              PathwayData(PV_FS, EXC, -66.0, (1.21, 1.18), (14.5, 1.7), "PV_FS-EXC"),
                              PathwayData(MC, EXC, -66, (0.5, 0.4), (12, 3), "MC-EXC"),
                              PathwayData(DISTAR_INH, EXC, -66, (0.5, 0.4), (12, 3), "DISTAR_INH-EXC")]
# "DISTAR_INH-EXC", "BC-EXC", "PV_FS-EXC", "MC-EXC"

exc_to_all_lumped_pathways = [PathwayData(EXC, BC, -66.0, (1.21, 1.18), (14.5, 1.7), "EXC-BC"),
                              PathwayData(EXC, PV_FS, -66.0, (1.21, 1.18), (14.5, 1.7), "EXC-PV_FS"),
                              PathwayData(EXC, MC, -66, (0.5, 0.4), (12, 3), "EXC-MC"),
                              PathwayData(EXC, INH_OTHER, -66, (0.5, 0.4), (12, 3), "EXC-INH_OTHER")]
# "EXC-BC", "EXC-PV_FS", "EXC-MC", "EXC-INH_OTHER"

all_pathways = exc_exc_pathways+exc_inh_pathways+inh_exc_pathways+inh_to_all_lumped_pathways+\
    exc_to_all_lumped_pathways+exc_exc_secondary_pathways
pathways_map = dict([(p.label, p) for p in all_pathways])

def get_pathway(label) :
    return pathways_map[label]

"""
pathways = {"L5_TTPC-L5_TTPC (Markram 97)":(L5_TTPC, L5_TTPC, -67.0),
            "L4_EXC-L4_EXC (Feldmeyer 04)":(L4_EXC, L4_EXC, -69.0),
            "L4_SS-L5_TTPC (Feldmeyer 05)":(L4_SS, L5_TTPC, -67.0),
            "L5_TTPC-L5_MC (Silberberg)":(L5_TTPC, 'MType.name=="L5_MC"', -70.0),
            "L5_STPC-L5_STPC (Le Be 06)":('MType.name=="L5_STPC"', 'MType.name=="L5_STPC"', -69.0),
            #"L2_PC-L2_PC (Feldmeyer 06)":(L2_PC, L2_PC, None),
            #"L23_PC-L23_MC (Lu 07)": ('MType.name=="L23_PC"', 'MType.name=="L23_MC"', None),
            #"L2_PC-L2_BTC (Koester 05)": (L2_PC, L2_BTC, None),
            #"L3_PC-L5_TTPC (Thomson 98)": (L3_PC, L5_TTPC, None),
            "L4_SS-L3_PC (Feldmeyer 02)": ('MType.name=="L4_SS"', L3_PC, -69.0),
            "L4_SS-L2_PC (Feldmeyer 02)": ('MType.name=="L4_SS"', L2_PC, -69.0),
            "L4_SS-L23_PC (Feldmeyer 02)": ('MType.name=="L4_SS"', 'MType.name=="L23_PC"', -69.0),
            "L23_PC-L23_PC (?)": ('MType.name=="L23_PC"', 'MType.name=="L23_PC"', -69.0)
            }
"""
