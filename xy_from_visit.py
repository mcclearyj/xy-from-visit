import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.table import Table
import os, re
import glob
import yaml
import astropy.coordinates as coord
from astropy.coordinates import SkyCoord
from astropy import units as u
import jwst
from jwst.datamodels import ImageModel
import pdb

# Local imports
from max_polygons import which_visit

class GrabXYCoords:
    """
    Utility to grab resampled single-visit mosaic XY coordinates from RA, Dec.

    TO DO
        - Incorporate a loop over desired bandpasses
        - Find a way to avoid looping over coordfile names 380,000 times
    """

    def __init__(self, catalog, visit_mosaics, config):
        self.catalog = catalog
        self.imcat = catalog[config['input_catalog']['hdu']].data
        self.ras = self.imcat[config['input_catalog']['ra_colname']]
        self.decs = self.imcat[config['input_catalog']['dec_colname']]
        self.visit_cat = {} # will hold
        self.visit_mosaics = visit_mosaics
        self.config = config
        self.output_cat = None

    def grab_coords(self, imcat, config):
        """
        Load in coordinates from catalog, return coord tuple. This is in here
        just in case it becomes useful later.
        Inputs
            imcat: FITS instance of catalog
            config: main run configuration dict
        """

        # Load in catalog
        cat_hdu = config['input_catalog']['hdu']
        imcat = imcat_fits[cat_hdu].read()

        # Grab RA, Dec
        ra_key = config['input_catalog']['ra_key']
        dec_key = config['input_catalog']['dec_key']
        imcat_ra = imcat[ra_key]; imcat_dec = imcat[dec_key]

        return (imcat_ra, imcat_dec)

    def convert_wcs2pix(self, imfile, ras, decs):
        """
        Use JWST ImageModel to convert the RA, Dec of galaxies that lie in the
        footprint of the given single-visit mosaic, to pixel X, Y. Thanks to Anton
        Koekemoer (@antonkoekemoer) for help here.

        Inputs
            imfile: image file to use for WCS
            ras, decs: astrometric coordinates

        Returns
            x, y: pixel coordinates
        """

        # Get header & build a WCS from it
        with ImageModel(imfile) as model:
            radec_to_xy = model.meta.wcs.get_transform('world', 'detector')
            xs, ys = radec_to_xy(ras, decs)

        # Return imcat_fits, now with corrected RA, Dec column
        return xs, ys

    def create_output_catalog(self, visits):
        """
        Create a dummy FITS catalog, which will be populated
        with RA, Dec, size measures from real catalog and X/Y from visit
        """
        imcat = self.imcat
        ras = self.ras
        decs = self.decs
        visits = np.array(visits, dtype=int)
        mcat_cols = self.config['output_catalog']['extra_cols']

        # These two will hold the pixel X, Y
        dummy_x = np.ones(len(imcat))
        dummy_y = np.ones(len(imcat))

        # Create Table instance and populate with columns from master cat
        tab = Table()
        for col in mcat_cols:
            tab.add_column(imcat[col], name=str(col))

        # Add columns that will represent the value added columns
        tab.add_columns(
            [visits, ras, decs, dummy_x, dummy_y],
            names=['visit_num', 'ra', 'dec', 'visit_X', 'visit_Y']
        )

        self.output_cat = tab

    def grab_matching_coordsfile(self, bandpass=None):
        """
        Little utility function to grab matching visit/footprint file (aka
        coordsfile or coords_file) for a given bandpass
        """
        # In case we ever want to supply an argument
        if bandpass == None:
            bandpass = self.config['bandpass']

        # Array of names for indexing
        coords_files = np.array(self.config['coord_files']['names'])

        # Identify coordsfile for bandpass name using regexps and list comprehension <3
        wg = [
            bandpass.lower() ==
            re.search(r"[f,F](\d){3}[w,W]", cfile).group().lower()
            for cfile in coords_files
        ]

        # Return the first matching coords_file
        return coords_files[wg][0]

    def assign_visit_number(self, this_coords_file):
        """
        Invoke which_visit() to assign a particular visit to every RA, Dec

        Input
            coords_file: contains footprint of every visit in this bandpass
        Returns
            visit numbers

        TO DO: loop over bandpasses!
        could rename visits as: bandpass_visit = [i + '_f277w' for i in visits]
        """
        ras = self.ras
        decs = self.decs

        coords_file = os.path.join(
            self.config['coord_files']['path'], this_coords_file
        )

        return which_visit(coords_file, ras, decs)

    def get_pixcoord_from_visit(self):
        """
        Couldn't think of a better name, but this will do the looping
        Saving this snippet in case I need it
        #unique_visits = [int(i) for i in np.unique(output_cat['visit_num'])]
        """
        # For convenience
        output_cat = self.output_cat
        # Loop over visits, reading in image WCS one at a time
        for visit_mosaic in self.visit_mosaics:

            # Friendly alert
            print(f"Working on mosaic {visit_mosaic}")

            # Find entries in catalog in this visit
            this_visit = int(os.path.basename(visit_mosaic).split('_')[1])
            wg = output_cat['visit_num'] == this_visit

            # Call to transform coords
            x, y = self.convert_wcs2pix(
                visit_mosaic, self.ras[wg], self.decs[wg]
            )

            # Replace coordinates
            output_cat['visit_X'][wg] = x
            output_cat['visit_Y'][wg] = y

        return

    def save_catalog(self):
        """ Save augmented catalog to file """

        outcatpath = os.path.join(
            self.config['output_catalog']['path'],
            self.config['output_catalog']['name']
        )

        self.output_cat.write(outcatpath, format='fits', overwrite=True)

    def run(self):
        """ Perform all functions """

        # Pick out matching coordsfile from bandpass
        this_coords_file = self.grab_matching_coordsfile()

        # Get corresponding visit numbers for every catalog entry
        visits = self.assign_visit_number(this_coords_file)

        # Create dummy output catalog
        self.create_output_catalog(visits)

        # Save to file as a pseudocheckpoint to at least save visit numbers
        self.save_catalog()

        # Loop over visit visits, select matching gals, get X, Y
        self.get_pixcoord_from_visit()

        # Save to file again
        self.save_catalog()
