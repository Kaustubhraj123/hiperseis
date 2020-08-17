"""
Formats the results of pointsets2grid into files that can be plotted
by GMT.
"""
import os
import json

import click
import numpy as np


def from_config(config_file):
    """
    Loads interpolation results generated by pointsets2grid and converts
    them to ASCII files that can be plotted by GMT. The files are output
    to the output directory specificed in the config, under a
    subdirectory 'gmt_data'.

    Files written:

      - {method_name}_loc: For each method in the config file, a 
        location file of format `LON LAT WEIGHT` is written. Each row
        is a station/sample location, and the weight is the total 
        relative weighting (dataset weight * sample weight if sample
        weights enabled, else dataset weight).
      - moho_grid: The interpolated depth grid of format `LON LAT DEPTH`.
        Is in a suitable format to be converted to a NetCDF grid by 
        GMT.
      - moho_gradient: The gradient grid of format
        `LON LAT ANGLE MAGNITUDE`. The lon/lat position is the start 
        of the vector tail, the angle is degrees counter-clockwise from
        horizontal and the magnitude is in decimal degrees.

    Parameters
    ----------
    config_file : str or bytes
        Path to the Moho workflow config file.
    """
    print("Writing data for GMT plotting")
    with open(config_file, 'r') as f:
        config = json.load(f)

    outdir = config.get('output_dir', os.getcwd())
    gmt_outdir = os.path.join(outdir, 'gmt_data')
    if not os.path.exists(gmt_outdir):
        os.mkdir(gmt_outdir)

    # Convert moho depth grid to GMT digestible format
    grid_data = os.path.join(outdir, 'moho_grid.csv')
    with open(grid_data, 'r') as fr:
        grid_ds = np.loadtxt(fr, delimiter=',', skiprows=3)
    # Remove std dev column
    grid_ds = np.delete(grid_ds, -1, 1)
    grid_data_gmt = os.path.join(gmt_outdir, 'moho_grid.txt')
    with open(grid_data_gmt, 'w') as fw:
        np.savetxt(fw, grid_ds, fmt=['%.6f', '%.6f', '%.2f'], delimiter=' ')

    # Do the same for gradient grid
    grad_data = os.path.join(outdir, 'moho_gradient.csv')
    with open(grad_data, 'r') as fr:
        grad_ds = np.loadtxt(fr, delimiter=',', skiprows=3)
    # Convert to polar coordinates
    r = np.sqrt(grad_ds[:, 2]**2 + grad_ds[:, 3]**2)
    t = np.arctan2(grad_ds[:, 3], grad_ds[:, 2])
    t *= 180.0/np.pi
    grad_ds[:, 2] = t
    grad_ds[:, 3] = r
    grad_data_gmt = os.path.join(gmt_outdir, 'moho_gradient.txt')
    with open(grad_data_gmt, 'w') as fw:
        np.savetxt(fw, grad_ds, fmt=['%.6f', '%.6f', '%.6f', '%.6f'], delimiter=' ')

    # Output network/method locations and sample weight * dataset weight
    # Total relative weighting can be used as symbol size on maps
    methods = config['methods']
    for method_params in methods:
        method = method_params['name']
        data = np.loadtxt(method_params['csv_file'], delimiter=',')
        # Remove depth column
        data = np.delete(data, 2, 1)
        weight = method_params['weighting']
        if method_params['enable_sample_weighting']:
            data[:, 2] *= weight
        # If sample weights not used, the weight column is the dataset weight
        else:
            try:
                data[:, 2].fill(weight)
            except IndexError:
                # Make weights column if it doesn't exist
                data = np.append(data, np.zeros_like(data[:, 1][:, np.newaxis]), axis=1)
                data[:, 2].fill(weight)
        outfile = os.path.join(gmt_outdir, f'{method}_loc.txt')
        with open(outfile, 'w') as fw:
            np.savetxt(fw, data, fmt=['%.6f', '%.6f', '%.2f'], delimiter= ' ')
    print(f"Complete! Data files saved to '{gmt_outdir}'")
 

@click.command()
@click.argument('config-file', type=click.Path(exists=True, dir_okay=False), required=True)
def main(config_file):
    from_config(config_file)


if __name__ == '__main__':
    main()
