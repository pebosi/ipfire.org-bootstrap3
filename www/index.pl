#!/usr/bin/perl

my $lang = "en";

# Set language to german, else use english site
if ($ENV{'HTTP_ACCEPT_LANGUAGE'} =~ /^de(.*)/) {
	$lang = "de";
}

print "Status: 302 Moved\n";
print "Pragma: no-cache\n";

if ($ENV{'SERVER_NAME'} eq "source.ipfire.org") {
	print "Location: /$lang/source.shtml\n";
} elsif ($ENV{'SERVER_NAME'} eq "tracker.ipfire.org") {
	print "Location: /$lang/tracker.shtml\n";
} else {
	print "Location: http://www.ipfire.org/$lang/index.shtml\n";
}

# End http header...
print "\n";
