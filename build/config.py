#!/usr/bin/python

import os
import time

config = {
	"title"       : "IPFire - Builder",
	"nightly_url" : "ftp://ftp.ipfire.org/pub/nightly-builds",
	"path"        : { "db" : "db", },
	"script"      : os.environ['SCRIPT_NAME'],
	"time"        : time.ctime(),
	"db_name"     : "builder.db",
}
