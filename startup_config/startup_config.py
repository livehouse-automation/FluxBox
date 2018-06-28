import configparser
import re
import ipaddress
import io
import sys
import subprocess
import os




class Logger(object):
    def __init__(self):
        pass
    def log(self, text):
        print(text)
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
        self.default_config['network'] = {}
        self.default_config['network']['ipv4_method'] = "dhcp"
        self.default_config['network']['ipv4_address'] = "0.0.0.0/0"
        self.default_config['network']['ipv4_gateway'] = "0.0.0.0"
        self.default_config['network']['dns_servers'] = '8.8.8.8, 8.8.4.4'
        self.default_config['network']['ntp_servers'] = '0.pool.ntp.org, 1.pool.ntp.org, 2.pool.ntp.org, 3.pool.ntp.org'
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

        elif section == 'network':
            if   item == 'ipv4_method':  return self.check_valid_ipv4_method
            elif item == 'ipv4_address': return self.check_valid_ipv4_interface
            elif item == 'ipv4_gateway': return self.check_valid_ipv4_address
            elif item == 'dns_servers': return self.check_valid_dns_servers
            elif item == 'ntp_servers': return self.check_valid_ntp_servers

            
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

    
    def check_valid_ipv4_interface(self, interface):
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




def get_connection_name(interface):
    nmcli_output = subprocess.run(["nmcli", "-terse", "-fields=DEVICE,CONNECTION", "device", "status"], stdout=subprocess.PIPE)
    nmcli_output = nmcli_output.stdout.decode("utf-8")
    nmcli_output = nmcli_output.split('\n')
    for x in nmcli_output:
        tmp = x.split(':')
        if len(tmp) == 2:
            i,c = tmp
            if i == interface:
                return c
    return None


def set_interface_dhcp(interface):
    c = get_connection_name(interface)
    output = list()
    output.append(subprocess.run(["nmcli", "-terse", "connection", "modify", c, "ipv4.method", "auto"], stdout=subprocess.PIPE))
    output.append(subprocess.run(["nmcli", "-terse", "connection", "modify", c, "ipv4.dns", ""], stdout=subprocess.PIPE))
    output.append(subprocess.run(["nmcli", "-terse", "connection", "modify", c, "ipv4.addresses", ""], stdout=subprocess.PIPE))
    output.append(subprocess.run(["nmcli", "-terse", "connection", "modify", c, "ipv4.gateway", ""], stdout=subprocess.PIPE))
    return output

    
def set_interface_static(interface, address, gateway, dns_servers):
    c = get_connection_name(interface)
    output = list()
    output.append(subprocess.run(["nmcli", "-terse", "connection", "modify", c, "ipv4.dns", ' '.join(dns_servers.replace(' ','').split(','))], stdout=subprocess.PIPE))
    output.append(subprocess.run(["nmcli", "-terse", "connection", "modify", c, "ipv4.addresses", address], stdout=subprocess.PIPE))
    output.append(subprocess.run(["nmcli", "-terse", "connection", "modify", c, "ipv4.gateway", gateway], stdout=subprocess.PIPE))
    output.append(subprocess.run(["nmcli", "-terse", "connection", "modify", c, "ipv4.method", "manual"], stdout=subprocess.PIPE))
    return output


def flap_interface(interface):
    c = get_connection_name(interface)
    output = list()
    output.append(subprocess.run(["nmcli", "-terse", "connection", "down", c], stdout=subprocess.PIPE))
    output.append(subprocess.run(["nmcli", "-terse", "connection", "up", c], stdout=subprocess.PIPE))
    return output
    
    
def set_hostname(hostname):
    return subprocess.run(["nmcli", "-terse", "general", "hostname", hostname], stdout=subprocess.PIPE)


def set_timezone(tz):
    return subprocess.run(["timedatectl", "set-timezone", tz], stdout=subprocess.PIPE)

    
    

# todo - stop heartbeat LED
L = Logger()         
configuration = LiveHouseBrickConfig("/media/boot/config.ini", L)

# set hostname
output = set_hostname(configuration.defined_config['system']['hostname'])
L.log(repr(output))

interface = 'eth0'

# set ip
if configuration.defined_config['network']['ipv4_method'] == 'dhcp':
    output = set_interface_dhcp(interface)
    for x in output:
        L.log(repr(x)) 
elif configuration.defined_config['network']['ipv4_method'] == 'static':
    output = set_interface_static(interface, 
                         configuration.defined_config['network']['ipv4_address'], 
                         configuration.defined_config['network']['ipv4_gateway'], 
                         configuration.defined_config['network']['dns_servers'])
    for x in output:
        L.log(repr(x))
        
output = flap_interface(interface)
for x in output:
    L.log(repr(x))

output = set_timezone(configuration.defined_config['system']['timezone'])
L.log(repr(output))
        
# todo - start heartbeat LED
# todo: do the heartbeat stuff in rc.local

