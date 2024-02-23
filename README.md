# xy-from-visit
Code to go from master catalog RA, Dec to catalog with  X/Y on a particular mosaic. Makes use of convex hull dcode kindly provided by Max Franco and WCS -> xy code provided by @antonkoekemoer 

![more_overlap_tileB9visit64](https://github.com/mcclearyj/xy-from-visit/assets/14120046/42cb0b25-ed88-4cba-88af-29d1b7d9ba71)

Figure description: DS9 image showing a sample of objects from Marko Shuntov's (@mShuntov) Tile B9 catalog that overlap the resampled visit 64 image created by Max Franco.

# To run:
```
python grab_XY_from_visit_runner.py -config xy_from_visit_config.yaml
```

Dependencies: `numpy`, `astropy`, `scipy`, `jwst`, `matplotlib`

# To-do

- Incorporate iteration over bandpasses for matching to different coordinate files
- Include bandpass in `visit_num` column of output catalog
- Fix hard-coded output catalog columns, or at least match convention of input master reference catalog to be used!

Longer term: find a cleverer way to sort through the different coordinate files, so that [we are not looping over thousands of entries]([url](https://github.com/mcclearyj/xy-from-visit/blob/5dbc3c943b2cd5e369893c4e3b1b3cf119649c7e/max_polygons.py#L90)https://github.com/mcclearyj/xy-from-visit/blob/5dbc3c943b2cd5e369893c4e3b1b3cf119649c7e/max_polygons.py#L90) for many hundreds of thousands of galaxies in four bandpasses. I added a break statement to at least stop looping once a match has been found, and also implemented `map()`, but this problem seems ripe for parallelization, at least (maybe `starmap()`?)
