#!/usr/bin/perl

print "Status: 302 Moved\n";
print "Pragma: no-cache\n";

if ($ENV{'SERVER_NAME'} eq "source.ipfire.org") {
	print "Location: /en/source.shtml\n";
} else {
	print "Location: /en/index.shtml\n";
}

# End http header...
print "\n";
