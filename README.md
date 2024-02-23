# xy-from-visit
Code to go from master catalog RA, Dec to catalog with  X/Y on a particular mosaic. Makes use of code kindly provided by Max Franco.

# To-do

- Incorporate iteration over bandpasses for matching to different coordinate files
- Include bandpass in `visit_num` column of output catalog
- Fix hard-coded output catalog columns, or at least match convention of input master reference catalog

Longer term: find a cleverer way to sort through the different coordinate files, so that we are not looping over thousands of entries for many hundreds of thousands of galaxies. 
