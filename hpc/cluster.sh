#!/usr/bin/env bash
#PBS -P vy72
#PBS -q normalbw
#PBS -l walltime=2:00:00,mem=256GB,ncpus=56,jobfs=100GB
#PBS -l wd
#PBS -j oe

module load python3/3.4.3 python3/3.4.3-matplotlib
module load hdf5/1.8.14p openmpi/1.8
module load geos/3.5.0 netcdf/4.4.1.1

# setup environment
export PATH=$HOME/.local/bin:$PATH
export PYTHONPATH=$HOME/.local/lib/python3.4/site-packages:$PYTHONPATH
export VIRTUALENVWRAPPER_PYTHON=/apps/python3/3.4.3/bin/python3
export LANG=en_AU.UTF-8
source $HOME/.local/bin/virtualenvwrapper.sh

# start the virtualenv
workon seismic

# gather
mpirun --mca mpi_warn_on_fork 0 cluster gather /g/data/ha3/sudipta/event_xmls -w "P S"


# sort
cluster sort outfile_P.csv 5. -s sorted_P.csv
cluster sort outfile_S.csv 10. -s sorted_S.csv

# match
# matching is an optional step as we can simply do P or S wave inversion
cluster match sorted_P.csv sorted_S.csv -p matched_P.csv -s matched_S.csv

# zones
# if matching is not performed, replace matched_P.csv by sorted_P.csv and
# matched_S.csv by sorted_P.csv
cluster zone '0 -50.0 100 190' matched_P.csv -r region_P.csv -g global_P.csv
cluster zone '0 -50.0 100 190' matched_S.csv -r region_S.csv -g global_S.csv

# alternative zone command using the param2x2, the parameter file used during
# inversion
# cluster zone -p /path/to/param2x2 matched_S.csv -r region_S.csv -g global_S.csv
