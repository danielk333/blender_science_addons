#!/usr/bin/env python

'''
Simulate scanning for objects
===============================
'''
import pickle

import numpy as np

import sorts
eiscat3d = sorts.radars.eiscat3d_interp

from sorts.scheduler import StaticList, ObservedParameters
from sorts.controller import Scanner
from sorts import SpaceObject
from sorts.profiling import Profiler
from sorts.radar.scans import Fence

end_t = 600.0
scan = Fence(azimuth=90, num=40, dwell=0.1, min_elevation=30)

p = Profiler()
logger = sorts.profiling.get_logger('scanning')

class ObservedScanning(StaticList, ObservedParameters):
    def generate_schedule(self, t, generator):
        datas = []
        for si, st in enumerate(self.radar.tx + self.radar.rx):
            datas.append(dict(
                pos = st.ecef.copy(),
                t = t,
                data = [],
            ))
        
        for ind, (radar, meta) in enumerate(generator):
            for si, st in enumerate(radar.tx + radar.rx):
                datas[si]['data'].append(st.pointing_ecef*100e3)

        return datas

scanner_ctrl = Scanner(
    eiscat3d, 
    scan, 
    t = np.arange(0, end_t, scan.dwell()), 
    profiler=p, 
    logger=logger,
)

p.start('total')
scheduler = ObservedScanning(
    radar = eiscat3d, 
    controllers = [scanner_ctrl], 
    logger = logger,
    profiler = p,
)

datas = scheduler.schedule()

p.stop('total')
print(p.fmt(normalize='total'))


with open('./radar_data.pickle', 'wb') as h:
    pickle.dump(datas, h)