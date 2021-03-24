import glob
import re

from pynpi import waveform

class Regression:
    def __init__(self,regression_path, use_gz=False, max_fsdbs=5000, half_clock=50):
        self.regression_path = regression_path
        self.use_gz = use_gz
                
        # signals_per_test[fsdb] = [signal-name:[values]]
        self.signals_per_test = {}
        
        self.signal_names = []
        
        self.fsdbs = []
        
        self.max_fsdbs = max_fsdbs
        self.find_fsdbs()
        
        self.half_clock = half_clock
        self.clock = 2 * self.half_clock
        
        
    def find_fsdbs(self):
        glob_pattern = '*/*.fsdb.gz' if self.use_gz else '*/*.fsdb'
        
        for fsdb_path in glob.iglob(self.regression_path + glob_pattern): #
            self.fsdbs.append(fsdb_path)
            
        print("found ", len(self.fsdbs), " fsdbs")
    
    # covers : list of Cover
    # Gets signal paths for events and items and extracts them from entire regression
    def extract_data(self, signal_names=[], scope_name='', sig_match_strings=[]):
        if (len(self.signal_names) == 0): 
            self.signal_names = signal_names
            
        if ((scope_name != '') and (len(sig_match_strings) > 0)):
            if (len(self.fsdbs) > 0):
                wave = waveform.open(self.fsdbs[0])
                self.signal_names.extend(self.get_matching_sigs(wave, scope_name, sig_match_strings))
            
        if (len(signal_names) == 0):
            print("No matching signals to extract found");
            return
        
        fsdbs_to_open = min(len(self.fsdbs)-1, self.max_fsdbs)
        
        for fsdb in self.fsdbs[:fsdbs_to_open]:
            self.extract_test_data(fsdb)
        
    def get_coverage_signals(self,covers):
        for cover in covers:
            self.signal_names.append(cover.event.signal.rtl_path)
            for item in cover.items:
                self.signal_names.append(item.signal.rtl_path)
        

    def extract_test_data(self, wave_location):
        wave = waveform.open(wave_location)

        if not wave:
            print("Error. Failed to open file: ", wave_location)
            return
       
        max_time = wave.max_time();
        
        signals_objects = [];
    
        self.signals_per_test[wave_location] = {}
    
        for signal in self.signal_names:
            signal_object = wave.sig_by_name(signal)
            self.signals_per_test[wave_location][signal] = waveform.sig_hdl_value_between(signal_object,0,max_time,waveform.VctFormat_e.DecStrVal)

        waveform.close(wave)
    
    # cover : Cover // should be list of Cover
    # cover_results[signal_name][relative_time][value] = {covered:True/False, by:[{test:"", at_time:0}]}
    def extract_cov(self, covers):
        for test,dataset in self.signals_per_test.items():
            for cover in covers:
                for event_value_change in dataset[cover.event.signal.rtl_path]:
                    if event_value_change[1] in cover.event.values:
                        cover.sample_cover(dataset, event_value_change[0])
                        

    def search(self, search_query):
        for test,dataset in self.signals_per_test.items():
            print("****** starting test: *******" + test)
            for event_value_change in dataset[search_query[0][0]]:
                if event_value_change[1] == str(search_query[0][1]):
                    #print("initial condition matched by test: " + test + " at time: " + str(event_value_change[0]))
                    match = True
                    for idx,term in enumerate(search_query[1:]):
                        signal_value = self.get_value_at(dataset, term[0], event_value_change[0] + self.half_clock, term[2])
                        if (signal_value != str(term[1])):
                            match = False
                            break
                        else:
                            print("condition " + str(idx+1) + " matched at time: " + str(event_value_change[0]))
                    
                    if match:
                        print("search criteria matched at time: ", str(event_value_change[0]))
                        return

    def get_value_at(self, dataset, rtl_path, event_time, sample_cycle):
        item_value_changes = dataset[rtl_path]
        last_change_b4_time = next(value_change for value_change in reversed(item_value_changes) if (value_change[0] < event_time + sample_cycle*self.clock))
        return last_change_b4_time[1]
                        
    def get_matching_sigs(self, fsdb, scope_name, sig_match_strings):
        scope = fsdb.scope_by_name(scope_name)
        regex = re.compile('|'.join(sig_match_strings))
    
        matching_sigs = []
    
        for sig in scope.sig_list():
            if regex.match(sig.full_name()):
                matching_sigs.append(sig.full_name())
            
        return matching_sigs
