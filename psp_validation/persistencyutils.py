"""Bundle of tools to help with persistifying data
"""

import os
import uuid
import numpy
import datetime


def jobdirname(trunk='.'):
    """Return a unique name for a job directory. Can be used as job ID.
    """
    return os.path.join(trunk, str(uuid.uuid4())+"_"+datetime.datetime.now().isoformat())


def mkjobdir(trunk='.'):
    """Make an output directory with a "unique" name
    """
    name = jobdirname(trunk)
    os.makedirs(name)
    return name


def dump_raw_traces_to_HDF5(h5file, pathway, data):
    """Dump a set of simulated psp traces to an HDF5 file.

    Parameters:
    hf: an h5py.File writable object
    pathway: string containing the pathway name
    data: array containing all the trace raw data

    The data format is:

    /pathways/<pathway names>/pairs/<pair id>

    Each data corresponds to a synaptic pair and sample contains an array of \
    shape (nsim, 2, npoints) where nsim is the number of simulations run for \
    a given pair, 2 corresponds to arrays with voltage and time measurements, \
    and npoints is the length of those two arrays. Each pair group has \
    attributes 'gid_pre' and 'gid_post' with the GIDs of each cell in the pair.

    Access example:

    pair0_rep1 = hf['pathways/SomePathway/pairs/0'][1]
    pair_0_rep0_v = hf['pathways/SomePathway/pairs/0'][0][0]
    pair_0_rep0_t = hf['pathways/SomePathway/pairs/0'][0][1]
    pair_0_pre_gid = hf['pathways/SomePathway/pairs/0'].attrs['gid_pre']
    pair_0_post_gid = hf['pathways/SomePathway/pairs/0'].attrs['gid_post']

    """
    for i, pair in enumerate(data):
        traces = [(t[0], t[1]) for t in pair] # strip out gids
        gids = pair[0][2]                     # (pre_gid, post_gid)
        group_name = 'pathways/%s/pairs/%i' % (pathway, i)
        h5file[group_name] = numpy.array(traces)
        h5file[group_name].attrs['gid_pre'] = gids[0]
        h5file[group_name].attrs['gid_post'] = gids[1]


def rotated_name(name):
    """Check if name exists as a file and rotate existing versions.

    Examples: given existing file.txt:

    Original file name   new file name
    ----------------------------------
    file.txt              file.txt.1
    file.txt.1            file.txt.2
    file.txt.2            file.txt.3

    """

    if not os.path.exists(name):
        return name

    base, ext = os.path.splitext(name)
    ext = ext[1:]
    if ext.isdigit():
        ext = str(int(ext) + 1)
    else:
        ext = '1'
    return rotated_name(base + '.' + ext)
