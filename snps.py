import glob
import re
import os
import timeit

from concurrent.futures import ThreadPoolExecutor

from pynpi import npisys
from pynpi import waveform

from coverage.regression import Regression

class SnpsRegression(Regression):

    def __init__(self,regression_path=os.getcwd(), use_gz=False, max_wave_files=5000, half_clock=50, num_threads=1):
        super(SnpsRegression,self).__init__(regression_path, use_gz, max_wave_files, half_clock, num_threads)

    def vendor_find_wave_files(self):
        glob_pattern = '*/*.fsdb.gz' if self.use_gz else '*/*.fsdb'
        
        for fsdb_path in glob.iglob(self.regression_path + glob_pattern): #
            self.wave_files.append(fsdb_path)
            
        print("found ", len(self.wave_files), " fsdbs")

    def vendor_get_signals(self,signal_groups):
        wave = waveform.open(self.wave_files[0])
        for signal_group in signal_groups:
            self.signal_names.extend(self.vendor_get_matching_sigs(signal_group, wave))
        waveform.close(wave)

    def vendor_get_matching_sigs(self, signal_group, fsdb):
        scope = fsdb.scope_by_name(signal_group.scope)
        regex = re.compile('|'.join(signal_group.match_strings))
    
        matching_sigs = []
    
        for sig in scope.sig_list():
            if regex.match(sig.full_name()):
                matching_sigs.append(sig.full_name())
            
        return matching_sigs

    def vendor_extract_wave_data(self, wave_location):
        wave = waveform.open(wave_location)

        if not wave:
            print("Error. Failed to open file: ", wave_location)
            return
       
        max_time = wave.max_time();
        
        signals_objects = [];
    
        self.signals_per_test[wave_location] = {}
    
        for signal in self.signal_names:
            signal_object = wave.sig_by_name(signal)
            self.signals_per_test[wave_location][signal] =waveform.sig_hdl_value_between(signal_object,0,max_time,waveform.VctFormat_e.DecStrVal)

        waveform.close(wave)
        
        print("finished extracting ", wave_location)

    def vendor_init(self):
     	if npisys.init(["something"]) != 0:
     		if npisys.init(["something"]) != 0: 
     		    return False;
     	return True

    def vendor_close(self):
     	npisys.end()
