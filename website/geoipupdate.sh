#!/bin/sh

URL="http://www.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz"
DST=/usr/local/share/GeoIP/

cd $DST
/usr/bin/wget -nd -r -N --progress=dot $URL
/bin/gunzip -f $DST/GeoIP.dat.gz --to-stdout > $DST/GeoIP.dat
