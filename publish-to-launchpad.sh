#!/bin/bash
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
#
# publish-to-launchpad.sh : publish sarracenia to launchpad account
#
#
# Code contributed by:
#  Khosrow Ebrahimpour - Shared Services Canada
#  Last Changed   : Dec 10 10:10:56 EST 2015
#  Last Revision  : Dec 10 10:10:56 EST 2015
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, 
#  but WITHOUT ANY WARRANTY; without even the implied warranty of 
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#

#
# Assumptions:
# 1. release.sh has been run and a new release made
# 
# Steps:
# 1. Rename the directory to conform to debian versioning
# 2. Update debian/changelog to reflect the distribution
# 3. Build source, sign and publish to launchpad


usage() {
	echo "`basename $0` <git tag> <distribution1> [<distribution2> ...]"
	echo 
	echo "Available distributions: preicse, trusty"

	exit 2
}

build() {
	DIST=$1
	TMPDIR=`mktemp --tmpdir=/tmp -d metpx-build.XXXX`	
	
	cd $P

	VERSION=`grep __version__ sarra/__init__.py | cut -c15- | sed -e 's/"//g'`
	DIR=metpx-sarracenia-${VERSION}
	CHNG=metpx-sarracenia_${VERSION}_source.changes

	cd ..
	cp -ap sarracenia $TMPDIR/$DIR
	cd $TMPDIR/$DIR
	sed -i "s/unstable; urgency/$DIST; urgency/g" debian/changelog
	debuild -S -uc -us
	if [ $? -gt 0 ]; then
		echo "Please resolve issues before proceeding with build!"
		exit 1
	fi
	cd $TMPDIR
	debsign -k4EE55EB5 $CHNG
	dput ppa:ssc-hpc-chp-spc/metpx $CHNG
	echo "-----"
	echo "Log files available at $TMPDIR"
	echo "-----"
}


if [ $# -lt 2 ]; then
	usage
	exit 2
fi

P=$PWD
TAG=$1

# Checkout the tagged version
cd $P
git checkout $TAG
if [ $? -gt 0 ]; then
	echo "Incorrect tag name!"
	exit 1
fi
shift

while (( $# )); do
	if [ $1 == 'precise' ]; then
		build precise
	elif [ $1 == 'trusty' ]; then
		build trusty
	else
		echo "Unknown distribution. `basename $0` currently only supports precise and trusty"
		cd $P
		git checkout master
		exit 1
	fi
	shift
done

# revert back to master
git checkout master
