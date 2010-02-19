#!/usr/bin/perl

use strict;
use IO::All;
use File::Copy;

### MAIN ###

my $counter = 0;
my %already_done = ();
my $action = undef;
if ($ARGV[0] eq "measure") {
	$action = \&measurement;
} elsif ($ARGV[0] eq "aggregate") {
	$action = \&aggregation;
} elsif ($ARGV[0] eq "analyze") {
	$action = \&analyzation;
} else {
	print STDERR "Usage: $0 [measure|aggregate|analyze]\n";
	exit 1;
}

# log
open(LF, ">vmesh_dumbbell_flowgrind_complete_test.log") or die "FATAL: Failed to open logfile\n";

# first, pure congestion
for (1 .. 10) {
	print LF $action->("congestion", 0, 0, $_, "qlimit");
}

# reordering, fixed rdelay
for (0 .. 50) {
	print LF $action->("reordering", $_, 30, 1000, "rrate");
}

# reordering, fixed rrate
for (0 .. 15) {
	print LF $action->("reordering", 5, 5 * $_, 1000, "rdelay");
}

# both, fixed rdelay, fixed limit
for (0 .. 50) {
	print LF $action->("both", $_, 30, 3, "rrate");
}

# both, fixed rrate, fixed limit
for (0 .. 15) {
	print LF $action->("both", "5", 5 * $_, 3, "rdelay");
}

# both, fixed rrate, fixed rdelay
for (1 .. 10) {
	print LF $action->("both", "5", 30, $_, "qlimit");
}

close(LF);

###########################
# Subroutines
###########################

sub analyzation ($$$$$) {
	my ($basename, $rrate, $rdelay, $qlimit, $variable) = @_;

	if ($already_done{"$basename$variable"}) {
		return;
	}

	if (-d "aggregated") {
		system("cd aggregated; vmesh_dumbbell_flowgrind_analysis.py --variable=$variable --type=$basename");
		my @pdfs = split("\n", `cd aggregated; ls *.pdf`);
		foreach my $pdf (@pdfs) {
			move("aggregated/$pdf", "$basename-$pdf");
		}
		$already_done{"$basename$variable"} = 1;
	} else {
		die "No aggregated data found.\nPlease use this script to aggregate, first.";
	}
}

sub aggregation ($$$$$) {
	my ($basename, $rrate, $rdelay, $qlimit, $variable) = @_;
	my $dirname = "$basename-var_$variable-rrate_$rrate-rdelay_$rdelay-qlimit_$qlimit";

	opendir(DIR, "$dirname") or die "FATAL: Failed to open directory $dirname: $?\n";
	my @ls = sort(readdir(DIR));
	closedir(DIR);

	unless (-d "aggregated") {
		$counter = 0;
		mkdir("aggregated") or die "Failed to create directory aggregated: $?";
	}

	my $tmp_cnt = 0;
	my $file = undef;
	foreach my $fn (@ls) {
		# no hidden files
		next if $fn =~ /^\./;
		if ($fn =~ /i([0-9]+)(_s[0-9]+_r[0-9]+_test_flowgrind)/) {
			$tmp_cnt = $1 + $counter;
			my $new_fn = sprintf("i%03d" . $2, $tmp_cnt);
			# prepend testbed params to file
			$file = io("$dirname/$fn");
			unshift(@{$file}, "testbed_param_variable=$variable");
			unshift(@{$file}, "testbed_param_reordering=$basename");
			unshift(@{$file}, "testbed_param_rrate=$rrate");
			unshift(@{$file}, "testbed_param_rdelay=$rdelay");
			unshift(@{$file}, "testbed_param_qlimit=$qlimit");
			# symlink file
			symlink("../$dirname/$fn", "aggregated/$new_fn");
		}
	}
	$counter = $tmp_cnt + 1;
}

sub measurement ($$$$$) {
	my ($basename, $rrate, $rdelay, $qlimit, $variable) = @_;
	my $dirname = "$basename-var_$variable-rrate_$rrate-rdelay_$rdelay-qlimit_$qlimit";

	# we want to return log information
	my $log = "==================================================================\n----------------------- Run: $dirname ---------------------\n\n";

	# calculate missing params
	my $rjitter = int($rdelay * 0.1);

	# configure toplogy for this test
	my $conffile = $ENV{'HOME'} . "/config/vmesh-helper/PARAMETERS.sh";
	my $config = '
DELAY="50ms"
DELAYJITTER="5ms"
DELAYCORRELATION="20%"

REORDERING="' . $rrate . '%"
REORDERDELAY="' . $rdelay . 'ms"
REORDERJITTER="' . $rjitter . 'ms"
REORDERDELAYCORRELATION="20%"

LIMIT="' . $qlimit . '"
';
	open(CF, ">$conffile") or die "FATAL: Failed to open conffile\n";
	print CF $config;
	close(CF);
	my $cmd = "um_vmesh -s -u -q " . $ENV{'HOME'} . "/config/um_vmesh_dumbbell-symmetric.conf 2>&1";
	$log .= "------------------- calling um_vmesh -------------------\n" . `$cmd`;

	# call measurement script
	$cmd = "vmesh_dumbbell_flowgrind_measurement.py -L $dirname 2>&1";
	$log .= "------------------- calling measurement script -------------------\n" . `$cmd`;

	return $log . "\n\n\n----------------------- END Run: $dirname ---------------------\n=================================================================\n\n\n";
}
