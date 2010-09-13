#!/usr/bin/perl

# K1------------                                                                        ------------ K2
#              |                                                                        |
# K3------------                                                                        ------------ K4
#              |- K9 ------ K10 ------ K11 ------ K12 ------ K13 ------ K14 ------ K15 -|
# K5------------           delay     reorder     limit     reorder     delay            ------------ K6
#              |            -->        -->                   <--        <--             |
# K7------------                                                                        ------------ K8
#
# kernel: K1 - K8                : -wolff
#         K10, K14               : default < 2.6.29
#         K11, K13               : -enhanced-netem
#         K9, K12, K15           : default

# globals
my $leaf_kernel       = "/home/schulte/checkout/linux/linux-2.6.31.x-um-schulte/vmlinux";
my $reorder_kernel    = "netem/vmeshnode-vmlinux-2.6.32.1-pae-um-enhanced-netem";
my $delay_kernel      = "default/vmeshnode-vmlinuz-2.6.24.7-pae-um";
my $default_kernel    = "default/vmeshnode-vmlinuz-2.6.32.12-pae-um";
my %nodes = (
	"1" => $leaf_kernel,
	"2" => $leaf_kernel,
	"3" => $leaf_kernel,
	"4" => $leaf_kernel,
	"5" => $leaf_kernel,
	"6" => $leaf_kernel,
	"7" => $leaf_kernel,
	"8" => $leaf_kernel,

    #in and out for queuing
	"9" => $default_kernel,
	"15" => $default_kernel,

    #queuing nodes
	"10" => $delay_kernel,
	"11" => $reorder_kernel,
	"12" => $default_kernel,
	"13" => $reorder_kernel,
	"14" => $delay_kernel,
);

sub startup() {
	for (sort(keys(%nodes))) {
		system("sudo", "um_xm", "-k", $nodes{$_}, "create", $ARGV[1] + $_);
	}
}

sub destroy() {
	for (sort(keys(%nodes))) {
        $nr = $ARGV[1] + $_;
		system("sudo", "xm", "destroy", "vmrouter$nr");
	}
}

sub waitforstartup() {
	my $up = "no";
	while ($up) {
		$up = `um_xm list 2>/dev/null | grep schulte | grep -v b-`;
		sleep 2;
	}
}

# main
if (($ARGV[1] >= 200) && ($ARGV[1] <= 300)) {
    if ($ARGV[0] eq "start") {
	    startup();
        waitforstartup();
    } elsif ($ARGV[0] eq "restart") {
        destroy();
	    startup();
        #waitforstartup();
        sleep 20;
    } elsif ($ARGV[0] eq "stop") {
	    destroy();
    } else {
	    print "Usage: start_dumbbell_2.pl {start|stop|restart} [offset: 200 to 300]\n\n"
    }
} else {
	print "Usage: start_dumbbell_2.pl {start|stop|restart} [offset: 200 to 300]\n\n"
}
