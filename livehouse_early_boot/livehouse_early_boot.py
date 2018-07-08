#!/usr/bin/python3

import configparser
import re
import ipaddress
import io
import sys
import subprocess
import os
import datetime
import argparse




class Logger(object):
    def __init__(self, logfile):
        self.logfile = open(logfile, 'w')
        pass
    def log(self, text):
        text = "%s: %s" % (datetime.datetime.now(), text)
        print(text)
        self.logfile.write("%s\n" % (text))
    def log_info(self,text):
        self.log(text)
    def log_error(self,text):
        self.log("ERROR: %s" % (text))
    def log_warning(self,text):
        self.log("WARNING: %s" % (text))




class LiveHouseBrickConfig(object):


    def __init__(self, inifile, logger):
        self.inifile = inifile
        self.logger = logger
        self.err = None
        self.set_defaults()

        # Prepare config to be applied
        self.defined_config = configparser.ConfigParser()
        self.defined_config['system'] = {}
        self.defined_config['network'] = {}

        # Open config file
        self.logger.log("Processing configuration file: '%s'" % (self.inifile))
        self.config_file = configparser.ConfigParser()
        self.config_file.read(self.inifile)

        # Process config file
        self.process_config()

        self.logger.log("Configuration defined:")
        self.print_config(self.defined_config)


    def print_config(self, c):
        x = io.StringIO()
        c.write(x)
        print(x.getvalue())


    def set_defaults(self):
        self.default_config = configparser.ConfigParser()
        self.default_config['system'] = {}
        self.default_config['system']['hostname'] = "livehousebrick"
        self.default_config['system']['timezone'] = "Australia/Perth"
        self.default_config['system']['ntp_servers'] = '0.pool.ntp.org, 1.pool.ntp.org, 2.pool.ntp.org, 3.pool.ntp.org'
        self.default_config['network'] = {}
        self.default_config['network']['ipv4_method'] = "dhcp"
        self.default_config['network']['ipv4_address'] = "0.0.0.0/0"
        self.default_config['network']['ipv4_netmask'] = "0.0.0.0"
        self.default_config['network']['ipv4_gateway'] = "0.0.0.0"
        self.default_config['network']['dns_servers'] = '8.8.8.8, 8.8.4.4'
        self.logger.log("Configuration defaults:")
        self.print_config(self.default_config)


    def process_config(self):
        for section in self.default_config.sections():
            for item in self.default_config[section].keys():
                self.defined_config[section][item] = self.process_section_item(section, item)
        

    def process_section_item(self, section, item):
        self.logger.log("Processing section '[%s]' item '%s'..." % (section, item))

        default_value = self.default_config[section][item]

        # check section present in config file
        if section not in self.config_file.sections():
            self.logger.log_error("Section '[%s]' missing from config file. Setting item '%s' to default value of '%s'." % (section, item, default_value))
            return default_value

        # check item present in config file
        if item not in self.config_file[section].keys():
            self.logger.log_warning("Section '[%s]' missing item '%s'. Using default value of '%s'." % (section, item, default_value))
            return default_value

        # get item value from config file
        item_value = self.config_file[section].get(item)

        # check item value is sane
        check_validity_function = self.get_check_validity_function(section, item)
        if check_validity_function(item_value):
            return item_value
        else:
            self.logger.log_error("Section '[%s]' item '%s' is invalid due to '%s'. Reverting to default value of '%s'." % (section, item, self.err, default_value))
            return default_value


    def get_check_validity_function(self, section, item):

        if section == 'system':
            if   item == 'hostname': return self.check_valid_hostname
            elif item == 'timezone': return self.check_valid_timezone
            elif item == 'ntp_servers': return self.check_valid_ntp_servers

        elif section == 'network':
            if   item == 'ipv4_method':  return self.check_valid_ipv4_method
            elif item == 'ipv4_address': return self.check_valid_ipv4_address
            elif item == 'ipv4_netmask': return self.check_valid_ipv4_netmask
            elif item == 'ipv4_gateway': return self.check_valid_ipv4_address
            elif item == 'dns_servers': return self.check_valid_dns_servers

            
    def check_valid_ntp_servers(self, serverlist):
        # check validity of each server
        return all(self.check_valid_hostname(x) for x in serverlist.replace(' ','').split(','))
    
    
    def check_valid_dns_servers(self, serverlist):
        # check validity of each server
        return all(self.check_valid_ipv4_address(x) for x in serverlist.replace(' ','').split(','))
        
            
    def check_valid_hostname(self, hostname):
        if len(hostname) > 255:
            self.err = "hostname has longer than 255 characters"
            return False
        allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        valid = all(allowed.match(x) for x in hostname.split("."))
        if not valid:
            self.err = "hostname has invalid characters; must only contain 'A-Z', 'a-z', '0-9', '-'; '.' allowed as separator"
        return valid
        

    def check_valid_ipv4_method(self, method):
        if method not in ('static', 'dhcp'):
            self.err = "must be set to either 'dhcp' or 'static'"
            return False
        return True

                
    def check_valid_ipv4_address(self, address):
        try:
            x = ipaddress.IPv4Address(address)
        except ipaddress.AddressValueError as err:
            self.err = err
            return False
        return True

    
    def check_valid_ipv4_netmask(self, netmask):
        interface = "%s/%s" % (self.defined_config['network']['ipv4_address'], netmask)
        try:
            x = ipaddress.IPv4Interface(interface)
        except ipaddress.NetmaskValueError as err:
            self.err = err
            return False
        except ipaddress.AddressValueError as err:
            self.err = err
            return False
        return True
    
    
    def check_valid_timezone(self, tz):
        if not os.path.exists(os.path.join('/usr/share/zoneinfo', tz)):
            self.err = "timezone not valid"
            return False
        return True


def set_interface_dhcp(interface, interface_file):
    with open(interface_file, 'w') as f:
        f.write("auto %s\n" % (interface))
        f.write("iface %s inet dhcp\n" % (interface))

    
def set_interface_static(interface, interface_file, address, netmask, gateway, dns_servers):
    with open(interface_file, 'w') as f:
        f.write("auto %s\n" % (interface))
        f.write("iface %s inet static\n" % (interface))
        f.write("    address %s\n" % (address))
        f.write("    netmask %s\n" % (netmask))
        f.write("    gateway %s\n" % (gateway))
        for s in dns_servers.split(','):
            s = s.strip()
            f.write("    dns-nameserver %s\n" % (s))

    
def set_hostname(hostname, hostname_file):
    with open(hostname_file, 'w') as f:
        f.write("%s\n" % (hostname))
    output = list()
    output.append(subprocess.run(["hostname", hostname], stdout=subprocess.PIPE))
    return output


def set_timezone(tz):
    return subprocess.run(["timedatectl", "set-timezone", tz], stdout=subprocess.PIPE)


def write_ntp_config(ntp_servers, ntp_configfile):
    output = list()
    with open(ntp_configfile, 'w') as f:
        f.write("driftfile /var/lib/ntp/ntp.drift\n")
        f.write("leapfile /usr/share/zoneinfo/leap-seconds.list\n")
        f.write("statistics loopstats peerstats clockstats\n")
        f.write("filegen loopstats file loopstats type day enable\n")
        f.write("filegen peerstats file peerstats type day enable\n")
        f.write("filegen clockstats file clockstats type day enable\n")
        for s in ntp_servers.replace(' ','').split(','):
            f.write("pool %s iburst\n" % (s))
            output.append(subprocess.run(["ntpdate", s], stdout=subprocess.PIPE))
        f.write("restrict -4 default kod notrap nomodify nopeer noquery limited\n")
        f.write("restrict -6 default kod notrap nomodify nopeer noquery limited\n")
        f.write("restrict 127.0.0.1\n")
        f.write("restrict ::1\n")
        f.write("restrict source notrap nomodify noquery\n")
    return output
      



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configini", help="config.ini file [/media/boot/config.ini]", type=str, default="/media/boot/config.ini")
    parser.add_argument("-i", "--interface_name", help="ethernet interface name [eth0]", type=str, default="eth0")
    parser.add_argument("-e", "--interface_config_file", help="interface configuration file [/etc/network/interfaces.d/eth0]", type=str, default="/etc/network/interfaces.d/eth0")
    parser.add_argument("-l", "--log_file", help="log file [/media/boot/config.log]", type=str, default="/media/boot/config.log")
    parser.add_argument("-n", "--ntp_config_file", help="ntp config file [/etc/ntp.conf]", type=str, default="/etc/ntp.conf")
    parser.add_argument("-o", "--hostname_file", help="hostname file [/etc/hostname]", type=str, default="/etc/hostname")
    parser.add_argument("action", help="action (start, stop, restart, etc). IGNORED.", type=str, default="ignored")
    args = parser.parse_args()
    print(repr(args))

    L = Logger(args.log_file)
    L.log("Started early boot config")
    configuration = LiveHouseBrickConfig(args.configini, L)

    # set hostname
    output = set_hostname(configuration.defined_config['system']['hostname'], args.hostname_file)
    L.log(repr(output))

    L.log("hostname configuration file '%s' contents:" %(args.hostname_file))
    with open(args.hostname_file, 'r') as f:
        L.log(f.read())

    # set ip
    if configuration.defined_config['network']['ipv4_method'] == 'dhcp':
        output = set_interface_dhcp(args.interface_name, args.interface_config_file)

    elif configuration.defined_config['network']['ipv4_method'] == 'static':
        output = set_interface_static(args.interface_name,
                                      args.interface_config_file,
                                      configuration.defined_config['network']['ipv4_address'],
                                      configuration.defined_config['network']['ipv4_netmask'],
                                      configuration.defined_config['network']['ipv4_gateway'],
                                      configuration.defined_config['network']['dns_servers'])

    L.log("Interface configuration file '%s' contents:" %(args.interface_config_file))
    with open(args.interface_config_file, 'r') as f:
        L.log(f.read())

    output = set_timezone(configuration.defined_config['system']['timezone'])
    L.log(repr(output))

    output = write_ntp_config(configuration.defined_config['system']['ntp_servers'], args.ntp_config_file)
    for x in output:
        L.log(repr(x))

    L.log("NTP configuration file '%s' contents:" %(args.ntp_config_file))
    with open(args.ntp_config_file, 'r') as f:
        L.log(f.read())

    L.log("Finished early boot config")
