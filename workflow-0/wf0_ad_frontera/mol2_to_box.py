#!/usr/bin/env python3
'''
Compute and emit the grid box parameters from a MOL2 file

Autodock needs to know the grid center and the number of grid
points in all 3 dimensions to define the grid box. In practice
the grid box may be defined in a MOL2 file that specifies
the 8 corners of the delimiting orthorhombus. This script
calculate the grid box parameters from the MOL2 file that
specifies the orthorhombus.
'''
import re

def parse_atom_line(line):
    '''
    Extract the x,y,z-coordinates from an ATOM line in MOL2 format.
    '''
    lst = str(line).split()
    xcoord = float(lst[2])
    ycoord = float(lst[3])
    zcoord = float(lst[4])
    return (xcoord,ycoord,zcoord)


def parse_file(lines):
    '''
    Extract a list of atomic coordinates from the lines in a MOL2 file.
    '''
    t3list = []
    pat_atom   = re.compile(r"@<TRIPOS>ATOM")
    pat_tripos = re.compile(r"@<TRIPOS>")
    doline = False
    for line in lines:
        if doline:
            if pat_tripos.match(line):
                break
            t3list.append(parse_atom_line(line))
        else:
            doline = pat_atom.match(line)
    return t3list

def find_minmax_coords(t3list):
    '''
    Find the minimum and maximum coordinates from the list of the coordinates.
    '''
    xmin =  1.0e+300
    xmax = -1.0e+300
    ymin =  1.0e+300
    ymax = -1.0e+300
    zmin =  1.0e+300
    zmax = -1.0e+300
    for (xcrd,ycrd,zcrd) in t3list:
        if xcrd < xmin:
            xmin = xcrd
        if xcrd > xmax:
            xmax = xcrd
        if ycrd < ymin:
            ymin = ycrd
        if ycrd > ymax:
            ymax = ycrd
        if zcrd < zmin:
            zmin = zcrd
        if zcrd > zmax:
            zmax = zcrd
    return (xmin,ymin,zmin,xmax,ymax,zmax)

def calc_grid_center(t6):
    '''
    Calculate grid center from coordinate minima and maxima
    '''
    (xmin,ymin,zmin,xmax,ymax,zmax) = t6
    xcnt = 0.5*(xmin+xmax)
    ycnt = 0.5*(ymin+ymax)
    zcnt = 0.5*(zmin+zmax)
    return (xcnt,ycnt,zcnt)

def calc_npoints(t6):
    '''
    Calculate the number of grid points in each dimension.

    The number of grid points always has to be an even number
    in Autodock. The default grid spacing is 0.375.
    '''
    spacing = 0.375
    factor  = 2
    (xmin,ymin,zmin,xmax,ymax,zmax) = t6
    xlen=(xmax-xmin)/spacing
    ylen=(ymax-ymin)/spacing
    zlen=(zmax-zmin)/spacing
    xnpts=int(xlen/float(factor)+1.0)*int(factor)
    ynpts=int(ylen/float(factor)+1.0)*int(factor)
    znpts=int(zlen/float(factor)+1.0)*int(factor)
    return (xnpts,ynpts,znpts)

def parse_arguments():
    '''
    Parse the arguments.
    '''
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("filename",help="MOL2 file to generate grid-box parameters from")
    args=parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_arguments()
    fobj = open(args.filename,"r")
    contents = fobj.readlines()
    fobj.close()
    t3list = parse_file(contents)
    t6 = find_minmax_coords(t3list)
    (xcen,ycen,zcen) = calc_grid_center(t6)
    (xpts,ypts,zpts) = calc_npoints(t6)
    print(f"{xcen:.5f},{ycen:.5f},{zcen:.5f} {xpts:d},{ypts:d},{zpts:d}")
