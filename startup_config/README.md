## Config file syntax

### [system] section
 * ```hostname``` can be set to either a single word hostname or an FQDN. Example ```livehousebrick```
 * ```timezone``` can be set to one of the tz database timezones listed here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List. Example ```Australia/Perth```

### [network] section
 * ```ipv4_method``` can be set to either ```static``` or ```dhcp```
 * ```ipv4_address``` only needs to be set if ```ipv4_method``` is set to ```static```. The IP address of this appliance. Syntax is <IP>/<maskbits> eg: ```192.168.69.69/24```
 * ```ipv4_gateway``` only needs to be set if ```ipv4_method``` is set to ```static```. The IP address of the default gateway. eg: ```192.168.69.1```
 * ```dns_servers``` only needs to be set if ```ipv4_method``` is set to ```static```. Comma separated list of DNS server IP addresses. eg: ```8.8.8.8,8.8.4.4```
 * ```ntp_servers``` Comma separated list of NTP server FQDNs or IPs.
