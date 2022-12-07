#!/bin/bash
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia/blob/master/doc/sr_subscribe.1.rst#documentation
#
# release.sh : create a new release of metpx-sarracenia
#
#
# Code contributed by:
#  Khosrow Ebrahimpour - Shared Services Canada
#  Last Changed   : Dec  9 11:27:17 EST 2015
#  Last Revision  : Dec  9 11:27:17 EST 2015
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
# 1. sarracenia/__init__.py exists and has the desired version number
# 
# Steps:
# 1. Update debian/changelog using "dch command"
# 2. Commit debian/changelog to git
# 3. perform 'git tag' operation using version provided


usage() {
	echo "`basename $0`  <release message>"
	echo 
	echo "Ex: `basename $0` 'releasing alpha1'"

	exit 2
}


if [ $# -ne 1 ]; then
	usage
fi

# VERSION=$1
MSG=$1

# Verify sarracenia/__init__.py has the same version
VERSION=`grep __version__ sarracenia/__init__.py | cut -c15- | sed -e 's/"//g'`

# Verify version format
if [[ ! $VERSION =~ ^[0-9]\.[0-9]{2}\.[0-9]{2} ]]; then	
	echo "ERROR: Version number must begin with P.YY.MM"	
	echo 
	echo "Where P is the numeric protocol version, YY is the year, and MM is the month"
	echo 
	echo "Please correct the version number in sarracenia/__init__.py"
	exit 1
fi


while [ 1 ]; do		
	read -e -p "Are you sure want to create release $VERSION? (y/n) " ANSWER
	case "$ANSWER" in
		Y|y)		
			echo "Proceeding with creation of metpx-sarracenia release $VERSION ..."
			sleep 2
			break
			;;
		N|n)		
			echo "Ok. Exitting!"
			exit 1
			;;
		*)
			echo "Please answer 'y' or 'n'."
			;;
	esac
done
		

#echo "dch -v $VERSION"
dch -v $VERSION

# echo "git commit debian/changelog -m 'cutting new release $VERSION'"
git commit debian/changelog -m "cutting new sarra release $VERSION"

# echo "git tag -a v$VERSION -m 'release $VERSION'"
git tag -a v$VERSION -m "sarracenia release $VERSION"

read -e -p "Enter the name of the git remote that you would like to push to: [default=origin] " -i "origin" REMOTE

# echo "git push origin master"
# echo "git push origin --tags"

git push $REMOTE main
git push $REMOTE --tags


echo "Please remember to add '+' to the version string in __init__.py!"
