import rebound
import numpy as np

def convert_archive(path):
    sa = rebound.SimulationArchive(path)
    print("Number of snapshots: %d" % len(sa))
    print("Time of first and last snapshot: %.1f, %.1f" % (sa.tmin, sa.tmax))

    positions = {}
    for si, sim in enumerate(sa):
        pos = np.zeros((3,len(sim.particles)))
        for pi, p in enumerate(sim.particles):
            pos[:,pi] = p.xyz
        positions[f'{si}'] = pos
    fout = '.'.join(path.split('.')[:-1] + ['npz'])
    np.savez(fout, **positions)
    print(f'Saved to {fout}')

if __name__=='__main__':
    import sys
    convert_archive(sys.argv[1])