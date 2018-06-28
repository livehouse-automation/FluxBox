import configparser
import re
import ipaddress
import io
import sys




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
        self.default_config['network']['ipv4_address'] = "0.0.0.0"
        self.default_config['network']['ipv4_netmask'] = "0.0.0.0"
        self.default_config['network']['ipv4_gateway'] = "0.0.0.0"
        self.default_config['network']['dns_method'] = "dhcp"
        self.default_config['network']['dns_servers'] = '8.8.8.8, 8.8.4.4'
        self.default_config['network']['ntp_servers'] = '0.pool.ntp.org, 1.pool.ntp.org, 2.pool.ntp.org, 3.pool.ntp.org'
        self.logger.log("Configuration defaults:")
        self.print_config(self.default_config)


    def process_config(self):
        for section in self.default_config.sections():
            for item in self.default_config[section].keys():
                self.defined_config[section][item] = self.process_section_item(section, item)
        

    def process_section_item(self, section, item):

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
            if item == 'hostname':
                return self.check_valid_hostname

        elif section == 'network':
            if   item == 'ipv4_method':  return self.check_valid_ipv4_method
            elif item == 'ipv4_address': return self.check_valid_ipv4_address
            elif item == 'ipv4_netmask': return self.check_valid_ipv4_netmask
            elif item == 'ipv4_gateway': return self.check_valid_ipv4_address
            elif item == 'dns_method': return self.check_valid_ipv4_method
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

    
    def check_valid_ipv4_netmask(self, netmask):
        try:
            x = ipaddress.IPv4Interface("%s/%s" % ('0.0.0.0', netmask))
        except ipaddress.NetmaskValueError as err:
            self.err = err
            return False
        return True


# todo - stop heartbeat LED
L = Logger()         
configuration = LiveHouseBrickConfig("/media/boot/config.ini", L)
# todo - start heartbeat LED
# todo: do the heartbeat stuff in rc.local

