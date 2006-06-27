#
# MCG Mesh Node Information
#

nodeinfos = {
	'xen'	: {
		'hostprefix' 	: 'xenmachine',
		'sender' 	: [11,22,23,24,25,26],
		'gw'		: [ 12+i for i in range(10)],
		'instbal'	: "/opt/vmesh/bin/instbal.sh",
		'dymoinst'	: "/opt/vmesh/dymo",
		'wlandev'	: "tap1",
		'imagepath'	: '/opt/mcg-mesh/images/gentoo/686/'
	},
	'mrouter' : {
		'hostprefix' 	: 'mrouter',
		'sender' 	: [i+1 for i in range(2)],
		'gw'		: [i+3 for i in range(3)],
		'instbal'	: "instbal.sh",
		'dymoinst'	: "/usr/local/sbin",
		'wlandev'	: "ath0",
		'imagepath'	: '/opt/mcg-mesh/images/gentoo/586/'
	}
}

#
# Fill up nodeinfo
#

for nodetype,data in nodeinfos.items():
	data['host'] 		= data['sender']+data['gw']
	data['gwc'] 		= len(data['gw'])
	data['senderc'] 	= len(data['sender'])
	data['hostc'] 		= len(data['host'])
