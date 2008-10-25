#!/usr/bin/python
###############################################################################
#                                                                             #
# IPFire.org - A linux based firewall                                         #
# Copyright (C) 2008  Michael Tremer & Christian Schmidt                      #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

import os
import time

config = {
	"title"       : "IPFire - Builder",
	"nightly_url" : ("ftp://ftp.ipfire.org/pub/nightly-builds/", "http://www.rowie.at/upload/ipfire/builds/",),
	"path"        : { "db" : "db", "log" : "error.log", },
	"script"      : os.environ['SCRIPT_NAME'],
	"db_name"     : "builder.db",
}

statedesc = {
	None : "",
	"unknown" : "Dunno what the host is doing at the moment...",
	"compiling" : "The host is really hard working at the moment...",
	"error" : "Oops! The host had an error...",
	"idle" : "The host is idle at the moment...",
}

ping2class = {
	True  : "online",
	False : "offline",
}

state2style = {
	None        : "",
	"compiling" : "background: #8C8; border: 1px solid #0e0;",
	"error"     : "background: #c33; border: 1px solid #e00;",
	"idle"      : "background: #ddd; border: 1px solid #eee;",
}
