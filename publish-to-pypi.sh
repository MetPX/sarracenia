#!/bin/bash
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
#
# publish-to-pypi.sh : publish sarracenia to PyPi
#
#
# Code contributed by:
#  Khosrow Ebrahimpour - Shared Services Canada
#  Last Changed   : Dec 10 13:17:03 EST 2015
#  Last Revision  : Dec 10 13:17:03 EST 2015
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
# 2. PyPi configuration is in place 
# 
# Steps:
# 1. build the wheel
# 2. upload the wheel to PyPi


usage() {
	echo "`basename $0 <git tag>`" 
	exit 2
}

if [ $# -ne 1 ]; then
	usage
	exit 2
fi

# checkout the tag version
git checkout $1


python3 setup.py bdist_wheel
if [ $# -ne 0 ]; then
	echo "Please fix errors and retry uploading to PyPi!"
	exit 1
fi

python3 setup.py bdist_wheel upload 

# checkout master again
git checkout master
