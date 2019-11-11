
# pcieutil.py
# Platform-specific PCIE status interface for SONIC
#

import os
import yaml
import subprocess
import re
import sys
from copy import deepcopy
try:
    from .pcie_base import PcieBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")
    


class PcieUtil(PcieBase):
    """Platform-specific PCIEutil class"""    
    # got the config file path
    def __init__(self, path):
        self.config_path = path

    # load the config file
    def load_config_file(self):
        config_file = self.config_path + "/" + "pcie.yaml"
        try:
            with open(config_file) as conf_file:
                self.confInfo = yaml.load(conf_file)
        except IOError as e:
            print "Error: {}".format(str(e))
            print "Not found config file, please add a config file manually, or generate it by running [show platform pcieinfo -g]"
            sys.exit()  

    # load current PCIe device
    def get_pcie_device(self):
        pciDict = {}
        pciList = []
        p1 = "^(\w+):(\w+)\.(\w)\s(.*)\s\(.*\)"
        p2 = "^.*:.*:.*:(\w+)\s\(.*\)"
        command1 = "sudo lspci"
        command2 = "sudo lspci -n"
        # run command 1
        proc1 = subprocess.Popen(command1, shell=True, stdout=subprocess.PIPE)
        output1 = proc1.stdout.readlines()
        (out, err) = proc1.communicate()
        # run command 2
        proc2 = subprocess.Popen(command2, shell=True, stdout=subprocess.PIPE)
        output2 = proc2.stdout.readlines()
        (out, err) = proc2.communicate()

        if proc1.returncode > 0:
            for line1 in output1:
                print(line1.strip())
            return
        elif proc2.returncode > 0:
            for line2 in output2:
                print(line2.strip())
            return
        else:
            for (line1, line2) in zip(output1, output2):
                pciDict.clear()
                match1 = re.search(p1, line1.strip())
                match2 = re.search(p2, line2.strip())
                if match1 and match2:
                    Bus = match1.group(1)
                    Dev = match1.group(2)
                    Fn = match1.group(3)
                    Name = match1.group(4)
                    Id = match2.group(1)
                    pciDict["name"] = Name
                    pciDict["bus"] = Bus
                    pciDict["dev"] = Dev
                    pciDict["fn"] = Fn
                    pciDict["id"] = Id 
                    pciList.append(pciDict)
                    pciDict = deepcopy(pciDict)
                else:
                    print("CAN NOT MATCH PCIe DEVICE")
        return pciList

  # check the current PCIe device with config file and return the result 
    def get_pcie_check(self):
        self.load_config_file()
        infoList = []
        infoDict = {}
        err = 0 
        curInfo = self.get_pcie_device()
        for item_conf in self.confInfo:
            flag = 0            
            bus_conf = item_conf["bus"]
            dev_conf = item_conf["dev"]
            fn_conf = item_conf["fn"]
            name_conf = item_conf["name"]
            id_conf = item_conf["id"]
            for item_cur in curInfo:
                bus_cur = item_cur["bus"]
                dev_cur = item_cur["dev"]
                fn_cur = item_cur["fn"]
                name_cur = item_cur["name"]
                id_cur = item_cur["id"]
                if bus_cur == bus_conf and dev_cur == dev_conf and \
                   fn_cur == fn_conf and name_cur == name_conf and \
                   id_cur == id_conf:
                   flag+=1
                   continue
            if flag:
                item_conf["result"] = "Passed"
            else:
                item_conf["result"] = "Failde"
                err+=1
        return self.confInfo
     
    # generate the config file with current pci device
    def dump_conf_yaml(self):
        curInfo = self.get_pcie_device()
        with open(self.config_path + "/" + "pcie.yaml", "w") as conf_file:
            yaml.dump(curInfo, conf_file, default_flow_style=False)
        print "generate pcie config file successfully ! ! !"
        return 
        
        
            



