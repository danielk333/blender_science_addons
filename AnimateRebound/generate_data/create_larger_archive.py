import rebound
import numpy as np

sim = rebound.Simulation()
sim.add(m=1.)
sim.add(m=1e-3, a=1, e=0.05)
sim.move_to_com()
sim.integrator = "whfast"
sim.dt = 0.05

N_testparticle = 1000
a_initial = np.linspace(1.1, 3, N_testparticle)
for a in a_initial:
    sim.add(a=a,f=np.random.rand()*2.*np.pi) # mass is set to 0 by default, random true anomaly

sim.N_active = 2

sim.automateSimulationArchive("big_archive.bin",interval=0.25,deletefile=True)

t_max = 100.*2.*np.pi
sim.integrate(t_max)