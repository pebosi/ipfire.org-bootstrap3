#!/usr/bin/perl

my $lang = "en";
my @error;

# Set language to german, else use english site
if ($ENV{'HTTP_ACCEPT_LANGUAGE'} =~ /^de(.*)/) {
	$lang = "de";
}

if($ENV{'REQUEST_METHOD'} eq 'GET') {
  @error = split(/=/, "$ENV{'QUERY_STRING'}");
}

print "Status: 302 Moved\n";
print "Pragma: no-cache\n";

if ($error[1]) {
	print "Location: /$lang/$error[1].shtml\n";
} else {
	if ($ENV{'SERVER_NAME'} eq "source.ipfire.org") {
		print "Location: /$lang/source.shtml\n";
	} else {
		print "Location: /$lang/index.shtml\n";
	}
}

# End http header...
print "\n";
