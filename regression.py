import glob
import re
import timeit

from concurrent.futures import ThreadPoolExecutor

from pynpi import waveform

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
    def __init__(self,regression_path, use_gz=False, max_fsdbs=5000, half_clock=50, num_threads=1):
        self.regression_path = regression_path
        self.use_gz = use_gz
        self.num_threads = num_threads
                
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
    def extract_data(self, signal_names=[], signal_groups=[]):
        if (len(self.signal_names) == 0): 
            self.signal_names = signal_names
            
        if (len(signal_groups) > 0):
            if (len(self.fsdbs) > 0):
                wave = waveform.open(self.fsdbs[0])
                for signal_group in signal_groups:
                    self.signal_names.extend(signal_group.get_matching_sigs(wave))
                waveform.close(wave)
            

        if (len(signal_names) == 0):
            print("No matching signals to extract found");
            return
        
        fsdbs_to_open = min(len(self.fsdbs)-1, self.max_fsdbs)

        start_time = timeit.default_timer()
        
        if self.num_threads == 1:
             for i, fsdb in enumerate(self.fsdbs[:fsdbs_to_open]):
                print("extracting data for ", fsdb, " test #", i, " out of: ", len(self.fsdbs))
                self.extract_test_data(fsdb)
        else:
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                for fsdb in self.fsdbs[:fsdbs_to_open]:
                    future = executor.submit(self.extract_test_data, fsdb)
        
        duration = timeit.default_timer() - start_time
        print("Took ", duration, " to extract data")
                
        
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
            self.signals_per_test[wave_location][signal] =waveform.sig_hdl_value_between(signal_object,0,max_time,waveform.VctFormat_e.DecStrVal)

        waveform.close(wave)
        
        print("finished extracting ", wave_location)
    
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
        

