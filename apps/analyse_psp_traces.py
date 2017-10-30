
import sys
if '.' not in sys.path :
    sys.path.append('.')

import os
import h5py
import numpy as np
from psp_validation import psp
from psp_validation import configutils as cu
import json
from collections import defaultdict

if __name__ == "__main__" :

    if len(sys.argv) == 2:
        dirname = sys.argv[1]
    else:
        print "This script needs one argument, the traces directory path"
        exit(1)

    configname = os.path.join(dirname, 'jobconfig.json')
    f = open(configname)
    cfg = cu.json2simconfig(f)
    f.close()

    bconfig = cfg.blue_config
    pways = cfg.pathways
    protocols = [cu.json2protocol(open(p)) for p in cfg.protocols]

    h5file = os.path.join(dirname, 'psp_traces.hdf5')
    f = open(h5file)
    h5data = h5py.File(h5file, 'r')

    class Summary(object) :
        pass

    summary = defaultdict(Summary)

    for pathwayname, protocol in zip(pways, protocols) :
    #for pathwayname in h5data['pathways/'].keys() :
        t_stim = protocol.t_stim
        t_start = t_stim - 10.
        spike_filter = psp.default_spike_filter(t_start)

        summary[pathwayname].amplitudes = list()
        summary[pathwayname].v = list()
        summary[pathwayname].t = list()
        pairs = h5data['pathways/%s/pairs' % (pathwayname)]
        for p in pairs.values() :
            pre_gid = p.attrs['gid_pre']
            post_gid = p.attrs['gid_post']
            syn_type = psp.synapse_type(bconfig, pre_gid)
            v_mean, t, vts, _ = psp.mean_pair_voltage_from_traces(p, spike_filter)
            ampl = psp.get_peak_amplitude(t,
                                          v_mean,
                                          t_start,
                                          t_stim,
                                          syn_type)
            summary[pathwayname].amplitudes.append(ampl)
            summary[pathwayname].v.append(v_mean)
            summary[pathwayname].t.append(t)
        np.savetxt('%s.csv' % (pathwayname), summary[pathwayname].amplitudes)
