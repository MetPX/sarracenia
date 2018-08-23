
# want a continuous feed, but of small files, so eliminate big ones.
# make sure it wants to download anything.

# want a continuous feed, but of small files, so eliminate big ones.
# tar files are big also.
reject .*\/\.tar
# GRIB files will overwhelm a small server.
reject .*grib2.*
# large netcdf files as well.
reject .*model_giops.*
# radar imagery
reject .*GIF.*

# reject moving targets (file overwritten in a matter of secs)
reject .*citypage.*
reject .*marine_weather.*
reject .*hydrometric.*
reject .*hourly.*
reject .*today.*
reject .*yesterday.*
