#!/usr/bin/perl

#    100M, 2ms                                                                            100M, 3ms
# K1------------                                                                        ------------ K2
#    100M, 5ms |                                                                        | 100M,10ms
# K3------------      100M       100M       2M          2M        100M       100M       ------------ K4
#    100M,20ms |- K9 ------ K10 ------ K11 ------ K12 ------ K13 ------ K14 ------ K15 -| 100M,20ms
# K5------------ delay     loss      reorder     limit     reorder     loss       delay ------------ K6
#    100M,20ms |  -->       -->        -->        <->        <--        <--        <--  | 100M,20ms
# K7------------                                  7,7                                   ------------ K8
#
# (Delays are set not in this script, but in the delay-1.sh and delay-2.sh scripts in the config folder)
#
# kernel: K1 - K8                : -lcd
#         K10, K14               : default < 2.6.29
#         K11, K13               : -enhanced-netem
#         K9, K12, K15           : default

# globals
my $leaf_kernel       = "lcd-kernel";  # <--- CHANGE!
my $reorder_kernel    = "netem/vmeshnode-vmlinux-2.6.32.1-pae-um-enhanced-netem";
my $delay_kernel      = "default/vmeshnode-vmlinux-2.6.27.54-pae-delay";
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

    #in and out for queuing -> delay
	"9" => $delay_kernel,
	"15" => $delay_kernel,

    #queuing nodes
	"10" => $default_kernel,
	"11" => $reorder_kernel,
	"12" => $default_kernel,
	"13" => $reorder_kernel,
	"14" => $default_kernel,
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
	    print "Usage: start_dumbbell.pl {start|stop|restart} [offset: 200 to 300]\n\n"
    }
} else {
	print "Usage: start_dumbbell.pl {start|stop|restart} [offset: 200 to 300]\n\n"
}
