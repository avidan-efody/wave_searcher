import glob
import re
import os
import timeit

from concurrent.futures import ThreadPoolExecutor

class SignalGroup:
    def __init__(self, scope, match_strings):
        self.scope = scope
        self.match_strings = match_strings

    def get_matching_sigs(self, fsdb):
        scope = fsdb.scope_by_name(self.scope)
        regex = re.compile('|'.join(self.match_strings))
    
        matching_sigs = []
    
        for sig in scope.sig_list():
            if regex.match(sig.full_name()):
                matching_sigs.append(sig.full_name())
            
        return matching_sigs

class Regression:
    def __init__(self,regression_path=os.getcwd(), 
                 use_gz=False, 
                 max_wave_files=5000, 
                 half_clock=50, 
                 num_threads=1):
        self.regression_path = regression_path
        self.use_gz = use_gz
        self.num_threads = num_threads
                
        # signals_per_test[fsdb] = [signal-name:[values]]
        self.signals_per_test = {}
        
        self.signal_names = []
        
        self.wave_files = []
        
        self.max_wave_files = max_wave_files
        self.vendor_find_wave_files()
        
        self.half_clock = half_clock
        self.clock = 2 * self.half_clock
        
        
    # covers : list of Cover
    # Gets signal paths for events and items and extracts them from entire regression
    def extract_data(self, signal_names=[], signal_groups=[]):
        if not self.vendor_init():
            print("vendor init failed")
            return

        if (len(self.signal_names) == 0): 
            self.signal_names = signal_names
            
        if (len(signal_groups) > 0):
            self.vendor_get_signals(signal_groups)

        if (len(signal_names) == 0):
            print("No matching signals to extract found");
            return
        
        waves_to_open = min(len(self.wave_files), self.max_wave_files)

        start_time = timeit.default_timer()
        
        if self.num_threads == 1:
             for i, wave_file in enumerate(self.wave_files[:waves_to_open]):
                print("extracting data for ", wave_file, " test #", i, " out of: ", len(self.wave_files))
                self.vendor_extract_wave_data(wave_file)
        else:
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                for wave_file in self.wave_files[:waves_to_open]:
                    future = executor.submit(self.vendor_extract_wave_data, wave_file)
        
        duration = timeit.default_timer() - start_time
        print("Took ", duration, " to extract data")

        self.vendor_close()
        
    def get_coverage_signals(self,covers):
        for cover in covers:
            self.signal_names.append(cover.event.signal.rtl_path)
            for item in cover.items:
                self.signal_names.append(item.signal.rtl_path)
        
    
    # cover : Cover // should be list of Cover
    # cover_results[signal_name][relative_time][value] = {covered:True/False, by:[{test:"", at_time:0}]}
    def extract_cov(self, covers):
        for test,dataset in self.signals_per_test.items():
            for cover in covers:
                for event_value_change in dataset[cover.event.signal.rtl_path]:
                    if event_value_change[1] in cover.event.values:
                        cover.sample(dataset, event_value_change[0])
                        

    def search(self, search_query):
        for test,dataset in self.signals_per_test.items():
            print("****** starting test: *******" + test)
            for event_value_change in dataset[search_query[0][0]]:
                if event_value_change[1] == str(search_query[0][1]):
                    match = True
                    for idx,term in enumerate(search_query[1:]):
                        signal_value = ''
                        if (isinstance(term[2],int)):
                            signal_value = self.get_value_at(dataset, term[0], event_value_change[0] + self.half_clock, term[2])
                            
                        if (isinstance(term[2],range)):
                            signal_value = self.get_value_over_range(dataset, term[0], event_value_change[0] + self.half_clock, term[2])
                            
                        if (signal_value != str(term[1])):
                            match = False
                            break
                        else:
                            print("condition " + str(idx+1) + " matched at time: " + str(event_value_change[0]))
                    
                    if match:
                        print("search criteria matched at time: ", str(event_value_change[0]))
                        return

    # return a value at a given point in time
    def get_value_at(self, dataset, rtl_path, event_time, sample_cycle):
        item_value_changes = dataset[rtl_path]
        last_change_b4_time = next(value_change for value_change in reversed(item_value_changes) if (value_change[0] < event_time + sample_cycle*self.clock))
        return last_change_b4_time[1]
    
    # returns a value only if it is the only value over the range specified
    def get_value_over_range(self, dataset, rtl_path, event_time, sample_range):
        item_value_changes = dataset[rtl_path]
        last_change_b4_range_start = next(value_change for value_change in reversed(item_value_changes) if (value_change[0] < event_time + sample_range.start*self.clock))
        last_change_b4_range_end = next(value_change for value_change in reversed(item_value_changes) if (value_change[0] < event_time + sample_range.stop*self.clock))
        if (last_change_b4_range_start[0] == last_change_b4_range_end[0]):
            return last_change_b4_range_start[1]
        else:
            return ''
        

    # These function are vendor specific
    def vendor_find_wave_files(self):
        pass

    def vendor_extract_wave_data(self, wave_location):
        pass

    def vendor_init(self):
        pass

    def vendor_close(self):
        pass