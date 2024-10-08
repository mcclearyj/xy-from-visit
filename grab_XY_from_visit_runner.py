import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.table import Table
import os, re
import glob
import yaml
from argparse import ArgumentParser

## Local imports
from xy_from_visit import GrabXYCoords

def read_yaml(yaml_file):
    """
    Load a YAML-format configuration file
    current package has a problem reading scientific notation as
    floats; see
    https://stackoverflow.com/questions/30458977/yaml-loads-5e-6-as-string-and-not-a-number
    """

    loader = yaml.SafeLoader

    loader.add_implicit_resolver(
        u'tag:yaml.org,2002:float',
        re.compile(u'''^(?:
        [-+]?(?:[0-9][0-9_]*)\\.[0-9_]*(?:[eE][-+]?[0-9]+)?
        |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)
        |\\.[0-9_]+(?:[eE][-+][0-9]+)?
        |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\\.[0-9_]*
        |[-+]?\\.(?:inf|Inf|INF)
        |\\.(?:nan|NaN|NAN))$''', re.X),
        list(u'-+0123456789.'))

    with open(yaml_file, 'r') as stream:
        # return yaml.safe_load(stream) # see above issue
        return yaml.load(stream, Loader=loader)

def parse_args():

    parser = ArgumentParser()

    parser.add_argument('-config', '-c', default=None,
                        help = 'Configuration file for this script')
    return parser.parse_args()

def main(args):

    # Load config
    config = read_yaml(args.config)

    # Create output directory, if it doesn't exist
    if os.path.isdir(config['output_catalog']['path']) == False:
        cmd = f"mkdir -p {config['output_catalog']['path']}"
        os.system(cmd)
    else:
        print(f"output directory {config['output_catalog']['path']} exists, continuing...")
    # Access master catalog and read it in
    master_cat = os.path.join(
        config['input_catalog']['path'], config['input_catalog']['name']
    )
    try:
        catalog = fits.open(master_cat)
    except FileNotFoundError as fnf:
        print("No catalog found\n", fnf)

    # Courtesy sanity check for requested output columns
    cols2save = config['output_catalog']['extra_cols']
    mcat_cols = catalog[config['input_catalog']['hdu']].header.values()
    for col in cols2save:
        if col not in mcat_cols:
            raise KeyError(f"Requested column {col} not in catalog, exiting...")

    # Locate single-visit mosaics
    visit_mosaic_path = os.path.join(
        config['visit_mosaic_path'], config['bandpass'], 'visit*20mas*i2d.fits*'
    )
    visit_mosaics = glob.glob(visit_mosaic_path)

    # Little sanity check #2: exit if no mosaics found!
    if len(visit_mosaics) == 0:
        raise FileNotFoundError(
            f"Warning: No mosaics found in {visit_mosaic_path}, exiting...\n"
        )
    else:
        print(f"Using visit mosaics {visit_mosaics}")

    # Create GrabXYCoords instance
    grab_xy_from_visit = GrabXYCoords(
        catalog = catalog,
        visit_mosaics = visit_mosaics,
        config = config
    )
    grab_xy_from_visit.run()

    return 0

if __name__ == '__main__':
    args = parse_args()
    rc = main(args)

    if rc == 0:
        print('grab_XY_from_visit_runner.py has completed succesfully')
    else:
        print(f'grab_XY_from_visit_runner.py has failed w/ rc={rc}')
