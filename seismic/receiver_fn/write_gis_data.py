"""
Generates geotiffs of the interpolated moho grid and gradient,
and shapefiles of the station/method locations.
"""
import os
import json

import click
import rasterio
import shapefile
import numpy as np


def _profile(data, nx, ny, bands=1, bounds=None):
    """
    Profile for writing depth and gradient. Dtype and band count needs
    to be set depending on data.
    """
    if bounds is not None:
        l, b, r, t = bounds
    else:
        l, b = np.min(data[:,0]), np.min(data[:,1])
        r, t = np.max(data[:,0]), np.max(data[:,1])

    with rasterio.Env():
        profile = rasterio.profiles.DefaultGTiffProfile()
        plate_carree = rasterio.crs.CRS.from_proj4(
            "+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 "
            "+datum=WGS84 +units=m +no_defs")
        transform = rasterio.transform.from_bounds(l, b, r, t, nx, ny)
        profile.update(crs=plate_carree, transform=transform, width=nx, height=ny,
                       count=bands, dtype=data.dtype)

    return profile


def write_depth_grid(config_file):
    print("Writing depth grid geotiff")
    with open(config_file, 'r') as fr:
        config = json.load(fr)
    
    outdir = config.get('output_dir', os.getcwd())
    grid_data = os.path.join(outdir, 'moho_grid.csv')
    with open(grid_data, 'r') as fr:
        nx = int(fr.readline())
        ny = int(fr.readline())
        grid_ds = np.loadtxt(fr, delimiter=',')

    bounds = config.get('bounds')
    gtiff_profile = _profile(grid_ds, nx, ny, bands=1, bounds=bounds)

    gis_outdir = os.path.join(outdir, 'gis_data')
    if not os.path.exists(gis_outdir):
        os.mkdir(gis_outdir)

    with rasterio.Env():
        # GDAL origin is top-left, so we need to flip the data so first element is top-left cell
        data = np.flipud(grid_ds[:, 2].reshape((ny, nx)))
        gtiff_profile.update(count=1, dtype=data.dtype)
        outfile = os.path.join(gis_outdir, 'moho_grid.tif')
        with rasterio.open(outfile, 'w', **gtiff_profile) as dst:
            dst.write(data, 1)

    print(f"Complete! File saved to '{outfile}'")


def write_gradient_grid(config_file):
    print("Writing gradient grid geotiff")
    with open(config_file, 'r') as fr:
        config = json.load(fr)
    
    outdir = config.get('output_dir', os.getcwd())
    grad_data = os.path.join(outdir, 'moho_gradient.csv')
    with open(grad_data, 'r') as fr:
        nx = int(fr.readline())
        ny = int(fr.readline())
        grad_ds = np.loadtxt(fr, delimiter=',')

    bounds = config.get('bounds')
    gtiff_profile = _profile(grad_ds, nx, ny, bands=2, bounds=bounds)

    gis_outdir = os.path.join(outdir, 'gis_data')
    if not os.path.exists(gis_outdir):
        os.mkdir(gis_outdir)

    with rasterio.Env():
        # GDAL origin is top-left, so we need to flip the data so first element is top-left cell
        u_data = np.flipud(grad_ds[:,2].reshape((ny, nx)))
        v_data = np.flipud(grad_ds[:,3].reshape((ny, nx)))
        gtiff_profile.update(count=2, dtype=u_data.dtype)
        outfile = os.path.join(gis_outdir, 'moho_gradient.tif')
        with rasterio.open(outfile, 'w', **gtiff_profile) as dst:
            dst.write(u_data, 1)
            dst.write(v_data, 2)

    print(f"Complete! File saved to '{outfile}'")


def write_sample_locations(config_file):
    methods = config_file['methods']
    for method_params in methods:

    
   

@click.command()
@click.argument('config-file', type=click.Path(exists=True, dir_okay=False), required=True)
@click.option('--depth', is_flag=True)
@click.option('--gradient', is_flag=True)
def main(config_file, depth, gradient):
    if depth:
        write_depth_grid(config_file)
    if gradient:
        write_gradient_grid(config_file)

if __name__ == '__main__':
    main()

