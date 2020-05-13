import os 
import numpy as np 
import parmed as pmd 
import simtk.openmm.app as app
import simtk.openmm as omm
import simtk.unit as u
from .utils import ContactMapReporter


def simulate_explicit(
        pdb_file, top_file, check_point=None, GPU_index=0, 
        output_traj="output.dcd", output_log="output.log", output_cm=None,
        temperature=300., 
        # ion_strength=0., 
        report_time=10, sim_time=10):
    """
    Start and run an OpenMM NPT simulation with Langevin integrator at 2 fs 
    time step and 300 K. The cutoff distance for nonbonded interactions were 
    set at 1.0 nm, which commonly used along with Amber force field. Long-range
    nonbonded interactions were handled with PME. 
    Water molecules and ions will be added to the system. 
    Parameters
    ----------
    top_file : topology file (.top, .prmtop, ...)
        This is the topology file discribe all the interactions within the MD 
        system. 
    pdb_file : coordinates file (.gro, .pdb, ...)
        This is the molecule configuration file contains all the atom position
        and PBC (periodic boundary condition) box in the system. 
    GPU_index : Int or Str 
        The device # of GPU to use for running the simulation. 
        Use Strings, '0,1' for example, to use more than 1 GPU
    output_traj : the trajectory file (.dcd)
        This is the file stores all the coordinates information of the MD 
        simulation results. 
    output_log : the log file (.log) 
        This file stores the MD simulation status, such as steps, time, 
        potential energy, temperature, speed, etc. 
    temperature : float, unit K 
        The temperature the simulation will be running under 
    ion_strength : float
        The ion concentration in the system, (to be implemented)
    report_time : 10 ps
        The frequency that program writes its information to the output in 
        picoseconds, 10^(-12) s
    sim_time : 10 ns
        The timespan of the simulation trajectory in nanoseconds, 10^(-9) s
    """

    top = pmd.load_file(top_file, xyz=pdb_file)

    system = top.createSystem(nonbondedMethod=app.PME, 
                              nonbondedCutoff=1*u.nanometer,
                              constraints=app.HBonds)
    dt = 0.002*u.picoseconds
    integrator = omm.LangevinIntegrator(temperature*u.kelvin, 1/u.picosecond, dt)
    system.addForce(omm.MonteCarloBarostat(1*u.bar, temperature*u.kelvin))

    try:
        platform = omm.Platform_getPlatformByName("CUDA")
        properties = {'DeviceIndex': str(GPU_index), 'CudaPrecision': 'mixed'}
    except Exception:
        platform = omm.Platform_getPlatformByName("OpenCL")
        properties = {'DeviceIndex': str(GPU_index)}

    simulation = app.Simulation(top.topology, system, integrator, platform, properties)

    simulation.context.setPositions(top.positions)

    simulation.minimizeEnergy()

    report_time = report_time * u.picoseconds
    report_freq = int(report_time/dt)
    simulation.context.setVelocitiesToTemperature(
        temperature*u.kelvin, np.random.randint(1, 10000))
    simulation.reporters.append(app.DCDReporter(output_traj, report_freq))
    if output_cm:
        simulation.reporters.append(ContactMapReporter(output_cm, report_freq))
    simulation.reporters.append(app.StateDataReporter(output_log,
            report_freq, step=True, time=True, speed=True,
            potentialEnergy=True, temperature=True, totalEnergy=True))
    simulation.reporters.append(app.CheckpointReporter('checkpnt.chk', report_freq))

    if check_point:
        simulation.loadCheckpoint(check_point)
    sim_time = sim_time * u.nanoseconds
    nsteps = int(sim_time/dt)
    simulation.step(nsteps)
    