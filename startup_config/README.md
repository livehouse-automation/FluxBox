## Config apply
 * Config file ```config.ini``` to be placed in ```/media/boot```
 * Script to be called via ```/etc/rc.local```
 * Script will read ```config.ini``` on boot, and apply settings
 * Output of script will be logged to ```/media/boot/config.log``` each boot
 * This is for troubleshooting - if system is inaccessable after boot, can pull SD card, put in another machine, read log file etc

## Config file syntax

### [system] section
 * ```hostname``` can be set to either a single word hostname or an FQDN. Example ```livehousebrick```
 * ```timezone``` can be set to one of the tz database timezones listed here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List. Example ```Australia/Perth```

### [network] section
 * ```ipv4_method``` can be set to either ```static``` or ```dhcp```
 * ```ipv4_address``` only needs to be set if ```ipv4_method``` is set to ```static```. The IP address of this appliance. Syntax is <IP>/<maskbits> eg: ```192.168.69.69/24```
 * ```ipv4_gateway``` only needs to be set if ```ipv4_method``` is set to ```static```. The IP address of the default gateway. eg: ```192.168.69.1```
 * ```dns_servers``` only needs to be set if ```ipv4_method``` is set to ```static```. Comma separated list of DNS server IP addresses. eg: ```8.8.8.8,8.8.4.4```
 * ```ntp_servers``` Comma separated list of NTP server FQDNs or IPs. eg: ```0.pool.ntp.org,1.pool.ntp.org,2.pool.ntp.org,3.pool.ntp.org```
