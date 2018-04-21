# aptly.
# problem: launchpad PPA only keeps latest version.  Would like a more comprehensive record that keeps old versions.
# aptly apparently has a way of doing this, according to:
#     https://groups.google.com/forum/#!topic/aptly-discuss/r4Vz2mwzEEM
# but not yet clear how exactly to do this...
# so far...
aptly repo create metpx-allversions

aptly repo -comment="my local MetPX mirror" edit metpx-allversions
aptly repo -dep-follow-all-variants=true edit metpx-allversions

aptly mirror update metpx-allversions
aptly mirror import metpx-allversions ppa:ssc-hpc-chp-spc/metpx

