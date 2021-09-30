import rebound
import numpy as np

sim = rebound.Simulation()
sim.add(m=1.)
sim.add(m=1e-3, a=1.)
sim.add(m=1e-3, a=1.9)
sim.move_to_com()
sim.dt = sim.particles[1].P*0.05  # timestep is 5% of orbital period
sim.integrator = "whfast"
sim.automateSimulationArchive("archive.bin",interval=0.25,deletefile=True)
sim.integrate(1e2)