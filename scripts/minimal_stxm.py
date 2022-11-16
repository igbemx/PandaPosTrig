from tango import DeviceProxy
import time
import numpy as np
import h5py

SLEEP = .01
FAST = 1000
MARGIN = 1.

panda = DeviceProxy('B318A-EA01/CTL/PandaPosTrig')
pi_x = DeviceProxy('B318A-EA01/CTL/PI_X')
pi_y = DeviceProxy('B318A-EA01/CTL/PI_Y')

def do_x_line(start=0, end=10, N=100, exptime=.009, latency=.001):

    panda.TrigAxis = 'X' # triger axis X or Y for horizontal and vertical respectively
    panda.TrigXPos = float(start) # position in microns
    panda.DetTimePulseStep = 1e3 * (exptime + latency)
    panda.DetTimePulseWidth = 1e3 * exptime
    panda.DetTimePulseN = N
    panda.TimePulsesEnable = True
    # panda.DetPosCapt = True
    panda.ArmSingle()

    # go to the starting positoin
    pi_x.Velocity = FAST
    pi_x.Position = start - MARGIN
    print('Going to X = %f ' % (start - MARGIN))
    while not pi_x.OnTarget:
        time.sleep(SLEEP)
    print('...there!')

    # do a controlled movement
    vel = (abs(start - end)) / (N * (exptime + latency))
    print('Scanning at velocity %e' % vel)
    pi_x.Velocity = vel
    pi_x.Position = end
    while (panda.PointNOut is None) or (len(panda.PointNOut) < N):
        time.sleep(SLEEP)
    print('...done!')

def do_stxm(x_start, x_end, y_start, y_end, Nx, Ny, exptime, latency,
            filename='/tmp/data.h5'):
    panda.DetPosCapt = True
    with h5py.File(filename, 'w') as fp:
        # create datasets for later
        shape = (Ny + 1, Nx)
        print('dataset shape', shape)
        x_dset = fp.create_dataset('x', shape=shape)
        y_dset = fp.create_dataset('y', shape=shape)
        pmt_dset = fp.create_dataset('pmt', shape=shape)
        diode_dset = fp.create_dataset('diode', shape=shape)

        for y_i, y_val in enumerate(np.linspace(y_start, y_end, Ny + 1)):
            pi_y.Position = y_val
            do_x_line(x_start, x_end, Nx, exptime, latency)
            print('    data shapes', panda.XPosOut.shape, panda.YPosOut.shape, panda.PMTOut.shape, panda.PDiodeOut.shape)
            x_dset[y_i, :] = panda.XPosOut[:Nx]  # needed for now, something weird with panda
            y_dset[y_i, :] = panda.YPosOut[:Nx]
            pmt_dset[y_i, :] = panda.PMTOut[:Nx]
            diode_dset[y_i, :] = panda.PDiodeOut[:Nx]
            fp.flush()
    panda.DetPosCapt = False
