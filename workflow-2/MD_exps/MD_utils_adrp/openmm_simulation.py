import os 
import time
import glob
import shutil 
import random
import numpy as np 

import parmed as pmd
import simtk.openmm.app as app
import simtk.openmm as omm
import simtk.unit as u

from MD_utils.openmm_reporter import ContactMapReporter
from MD_utils.utils import create_md_path, touch_file


def openmm_simulate_amber_implicit(
        pdb_file, 
        top_file=None, 
        check_point=None, 
        GPU_index=0,
        output_traj="output.dcd", 
        output_log="output.log", 
        output_cm=None,
        report_time=10*u.picoseconds, 
        sim_time=10*u.nanoseconds,
        reeval_time=None, 
        ):
    """
    Start and run an OpenMM NVT simulation with Langevin integrator at 2 fs 
    time step and 300 K. The cutoff distance for nonbonded interactions were 
    set at 1.2 nm and LJ switch distance at 1.0 nm, which commonly used with
    Amber force field. Long-range nonbonded interactions were handled with PME.  

    Parameters
    ----------
    pdb_file : coordinates file (.gro, .pdb, ...)
        This is the molecule configuration file contains all the atom position
        and PBC (periodic boundary condition) box in the system. 
   
    check_point : None or check point file to load 
        
    GPU_index : Int or Str 
        The device # of GPU to use for running the simulation. Use Strings, '0,1'
        for example, to use more than 1 GPU
  
    output_traj : the trajectory file (.dcd)
        This is the file stores all the coordinates information of the MD 
        simulation results. 
  
    output_log : the log file (.log) 
        This file stores the MD simulation status, such as steps, time, potential
        energy, temperature, speed, etc.
 
    output_cm : the h5 file contains contact map information

    report_time : 10 ps
        The program writes its information to the output every 10 ps by default 

    sim_time : 10 ns
        The timespan of the simulation trajectory
    """

    # set up save dir for simulation results 
    work_dir = os.getcwd() 
    time_label = int(time.time())
    omm_path = create_md_path(time_label) 
    print(f"Running simulation at {omm_path}")

    # setting up running path  
    os.chdir(omm_path)

    if top_file: 
        pdb = pmd.load_file(top_file, xyz = pdb_file)
        shutil.copy2(top_file, './')
        system = pdb.createSystem(nonbondedMethod=app.CutoffNonPeriodic, 
                nonbondedCutoff=1.0*u.nanometer, constraints=app.HBonds, 
                implicitSolvent=app.OBC1)
    else: 
        pdb = pmd.load_file(pdb_file)
        forcefield = app.ForceField('amber99sbildn.xml', 'amber99_obc.xml')
        system = forcefield.createSystem(pdb.topology, 
                nonbondedMethod=app.CutoffNonPeriodic, 
                nonbondedCutoff=1.0*u.nanometer, constraints=app.HBonds)

    dt = 0.002*u.picoseconds
    integrator = omm.LangevinIntegrator(300*u.kelvin, 91.0/u.picosecond, dt)
    integrator.setConstraintTolerance(0.00001)

    try:
        platform = omm.Platform_getPlatformByName("CUDA")
        properties = {'DeviceIndex': str(GPU_index), 'CudaPrecision': 'mixed'}
    except Exception:
        platform = omm.Platform_getPlatformByName("OpenCL")
        properties = {'DeviceIndex': str(GPU_index)}

    simulation = app.Simulation(pdb.topology, system, integrator, platform, properties)

    if pdb.get_coordinates().shape[0] == 1: 
        simulation.context.setPositions(pdb.positions) 
        shutil.copy2(pdb_file, './')
    else: 
        positions = random.choice(pdb.get_coordinates())
        simulation.context.setPositions(positions/10) 
        #parmed \AA to OpenMM nm
        pdb.write_pdb('start.pdb', coordinates=positions) 

    # equilibrate
    simulation.minimizeEnergy() 
    simulation.context.setVelocitiesToTemperature(300*u.kelvin, random.randint(1, 10000))
    simulation.step(int(100*u.picoseconds / (2*u.femtoseconds)))

    # setting up reports 
    report_freq = int(report_time/dt)
    simulation.reporters.append(app.DCDReporter(output_traj, report_freq))
    if output_cm:
        simulation.reporters.append(ContactMapReporter(output_cm, report_freq))
    simulation.reporters.append(app.StateDataReporter(output_log,
            report_freq, step=True, time=True, speed=True,
            potentialEnergy=True, temperature=True, totalEnergy=True))
    simulation.reporters.append(app.CheckpointReporter('checkpnt.chk', report_freq))

    if check_point:
        simulation.loadCheckpoint(check_point)

    if reeval_time: 
        nsteps = int(reeval_time/dt) 
        niter = int(sim_time/reeval_time) 
        for i in range(niter): 
            if os.path.exists('../halt'): 
                return 
            elif os.path.exists('new_pdb'):
                print("Found new.pdb, starting new sim...") 

                # cleaning up old runs 
                del simulation
                # starting new simulation with new pdb
                with open('new_pdb', 'r') as fp: 
                    new_pdb = fp.read().split()[0] 
                os.chdir(work_dir)
                openmm_simulate_amber_implicit(
                        new_pdb, top_file=top_file, 
                        check_point=None, 
                        GPU_index=GPU_index,
                        output_traj=output_traj, 
                        output_log=output_log, 
                        output_cm=output_cm,
                        report_time=report_time, 
                        sim_time=sim_time,
                        reeval_time=reeval_time, 
                        )
            else: 
                simulation.step(nsteps)
    else: 
        nsteps = int(sim_time/dt)
        simulation.step(nsteps)

    os.chdir(work_dir)
    if not os.path.exists('../halt'): 
        openmm_simulate_amber_implicit(
                pdb_file, top_file=top_file, 
                check_point=None, 
                GPU_index=GPU_index,
                output_traj=output_traj, 
                output_log=output_log, 
                output_cm=output_cm,
                report_time=report_time, 
                sim_time=sim_time,
                reeval_time=reeval_time, 
                )
    else: 
        return  


def openmm_simulate_amber_explicit(
        pdb_file, 
        top_file=None, 
        check_point=None, 
        GPU_index=0,
        output_traj="output.dcd", 
        output_log="output.log", 
        output_cm=None,
        report_time=10*u.picoseconds, 
        sim_time=10*u.nanoseconds,
        reeval_time=None, 
        ):
    """
    Start and run an OpenMM NPT simulation with Langevin integrator at 2 fs 
    time step and 300 K. The cutoff distance for nonbonded interactions were 
    set at 1.0 nm, which commonly used along with Amber force field. Long-range
    nonbonded interactions were handled with PME. 

    Parameters
    ----------
    top_file : topology file (.top, .prmtop, ...)
        This is the topology file discribe all the interactions within the MD 
        system. 

    pdb_file : coordinates file (.gro, .pdb, ...)
        This is the molecule configuration file contains all the atom position
        and PBC (periodic boundary condition) box in the system. 

    GPU_index : Int or Str 
        The device # of GPU to use for running the simulation. Use Strings, '0,1'
        for example, to use more than 1 GPU

    output_traj : the trajectory file (.dcd)
        This is the file stores all the coordinates information of the MD 
        simulation results. 

    output_log : the log file (.log) 
        This file stores the MD simulation status, such as steps, time, potential
        energy, temperature, speed, etc.

    report_time : 10 ps
        The program writes its information to the output every 10 ps by default 

    sim_time : 10 ns
        The timespan of the simulation trajectory
    """

    # set up save dir for simulation results 
    work_dir = os.getcwd() 
    time_label = int(time.time())
    omm_path = create_md_path(time_label) 
    print(f"Running simulation at {omm_path}")

    # setting up running path  
    os.chdir(omm_path)

    top = pmd.load_file(top_file, xyz = pdb_file)

    system = top.createSystem(nonbondedMethod=app.PME, nonbondedCutoff=1*u.nanometer,
                              constraints=app.HBonds)
    dt = 0.002*u.picoseconds
    integrator = omm.LangevinIntegrator(300*u.kelvin, 1/u.picosecond, dt)
    system.addForce(omm.MonteCarloBarostat(1*u.bar, 300*u.kelvin))

    try:
        platform = omm.Platform_getPlatformByName("CUDA")
        properties = {'DeviceIndex': str(GPU_index), 'CudaPrecision': 'mixed'}
    except Exception:
        platform = omm.Platform_getPlatformByName("OpenCL")
        properties = {'DeviceIndex': str(GPU_index)}

    simulation = app.Simulation(top.topology, system, integrator, platform, properties)

    # simulation.context.setPositions(top.positions)
    if top.get_coordinates().shape[0] == 1: 
        simulation.context.setPositions(top.positions) 
        shutil.copy2(pdb_file, './')
    else: 
        positions = random.choice(top.get_coordinates())
        simulation.context.setPositions(positions/10) 
        #parmed \AA to OpenMM nm
        top.write_pdb('start.pdb', coordinates=positions) 

    simulation.minimizeEnergy()
    simulation.context.setVelocitiesToTemperature(300*u.kelvin, random.randint(1, 10000))
    simulation.step(int(100*u.picoseconds / (2*u.femtoseconds)))

    report_freq = int(report_time/dt)
    simulation.reporters.append(app.DCDReporter(output_traj, report_freq))
    if output_cm:
        simulation.reporters.append(ContactMapReporter(output_cm, report_freq))
    simulation.reporters.append(app.StateDataReporter(output_log,
            report_freq, step=True, time=True, speed=True,
            potentialEnergy=True, temperature=True, totalEnergy=True))
    simulation.reporters.append(app.CheckpointReporter('checkpnt.chk', report_freq))

    if check_point:
        simulation.loadCheckpoint(check_point)
    nsteps = int(sim_time/dt)
    simulation.step(nsteps)

    if reeval_time: 
        nsteps = int(reeval_time/dt) 
        niter = int(sim_time/reeval_time) 
        for i in range(niter): 
            if os.path.exists('../halt'): 
                return 
            elif os.path.exists('new_pdb'):
                print("Found new.pdb, starting new sim...") 

                # cleaning up old runs 
                del simulation
                # starting new simulation with new pdb
                with open('new_pdb', 'r') as fp: 
                    new_pdb = fp.read().split()[0] 
                os.chdir(work_dir)
                openmm_simulate_amber_explicit(
                        new_pdb, top_file=top_file, 
                        check_point=None, 
                        GPU_index=GPU_index,
                        output_traj=output_traj, 
                        output_log=output_log, 
                        output_cm=output_cm,
                        report_time=report_time, 
                        sim_time=sim_time,
                        reeval_time=reeval_time, 
                        )
            else: 
                simulation.step(nsteps)
    else: 
        nsteps = int(sim_time/dt)
        simulation.step(nsteps)

    os.chdir(work_dir)
    if not os.path.exists('../halt'): 
        openmm_simulate_amber_explicit(
                pdb_file, top_file=top_file, 
                check_point=None, 
                GPU_index=GPU_index,
                output_traj=output_traj, 
                output_log=output_log, 
                output_cm=output_cm,
                report_time=report_time, 
                sim_time=sim_time,
                reeval_time=reeval_time, 
                )
    else: 
        return  
