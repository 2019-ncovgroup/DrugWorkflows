from simtk.openmm.app import *
from simtk.openmm import *
from simtk.unit import *
import sys

prmtop = AmberPrmtopFile('../../../build/complex.prmtop')
system = prmtop.createSystem(nonbondedMethod=PME, nonbondedCutoff=1.2*nanometer, constraints=HBonds)
force = CustomExternalForce("scale*k*unit*((periodicdistance(x, y, z, x0, y0, z0))^2)")
force.addGlobalParameter("unit", 1.0*kilocalories_per_mole/angstrom**2)
force.addGlobalParameter("scale", 0.0) # to control the strength of restraint
system.addForce(force)
platform = Platform.getPlatformByName('CUDA')
properties = {'Precision': 'mixed'}
#properties = {'Precision': 'mixed', 'DisablePmeStream': '\'true\''}
integrator = LangevinIntegrator(300*kelvin, 5/picosecond, 0.002*picoseconds)
system.addForce(MonteCarloBarostat(1.01325*bar, 300*kelvin, 25))
simulation = Simulation(prmtop.topology, system, integrator, platform, properties)
simulation.loadState('../equilibration/eq2.xml')

simulation.reporters.append(DCDReporter('sim1.dcd', 10000))
simulation.reporters.append(StateDataReporter('sim1.log', 10000, step=True, potentialEnergy=True, temperature=True))

# Simulation
simulation.step(50000)
simulation.saveState('sim1.xml')

