import itertools

class Signal:
    def __init__(self, rtl_path, logical_name=""):
        self.rtl_path = rtl_path
        
        if (logical_name != ""):
            self.logical_name = logical_name
        else:
            pass
            #self.logical_name = re.match('([^\.^\/]*)$', rtl_path).group(1)
            
class Event:
    # signal: Signal
    # values: when signal value in [values] the event is emitted
    def __init__(self, signal, values):
        self.signal = signal
        self.values = [str(v) for v in values]
        
class CoverItem:
    # signal : Signal
    # sample_cycles : cycles from event
    def __init__(self, signal, sample_cycles, buckets):
        self.signal = signal
        self.sample_cycles = sample_cycles
        self.buckets = buckets
        
    def buckets_at_sample_cycle(self):
        result = []
        
        for bucket in self.buckets:
            for sample_cycle in self.sample_cycles:
                result.append(str(bucket) + '@' + str(sample_cycle))
                
        return result
    
class Cover:
    # event: Event
    # items : list of CoverItem
    # crosses : list of list of CoverItem
    def __init__(self,event,items,crosses):
        self.event = event
        self.items = items
        self.crosses = crosses
        
        self.cross_items_buckets = []
        self.create_empty();
        
        
    # bucket name for cross: mispredict_X_snoop[1@(-2),1@(0)]
    def create_empty(self):
        self.cover_hash = {}
        
        for item in self.items:
            self.cover_hash[item.signal.logical_name] = {}
            for sample_cycle in item.sample_cycles:
                self.cover_hash[item.signal.logical_name][sample_cycle] = {}
                for bucket in item.buckets:
                    self.cover_hash[item.signal.logical_name][sample_cycle][bucket] = False
                    
        for cross in self.crosses:
            cover_name = '_X_'.join([item.signal.logical_name for item in cross])
            self.cover_hash[cover_name] = {}
            for item in cross:
                self.cross_items_buckets.append(item.buckets_at_sample_cycle())
            
            for cross_bucket in list(itertools.product(*self.cross_items_buckets)):
                cross_bucket_name = ','.join(cross_bucket)
                self.cover_hash[cover_name][cross_bucket_name] = False            
                
    def sample_cover(self, dataset, event_time):
        for item in self.items:
            for sample_cycle in item.sample_cycles:
                value = self.get_value_at(dataset, item.signal.rtl_path, event_time, sample_cycle)
                for bucket in item.buckets:
                    if value in bucket:
                        self.cover_hash[item.signal.logical_name][sample_cycle][bucket] = True
                
    def get_value_at(self, dataset, rtl_path, event_time, sample_cycle):
        item_value_changes = dataset[rtl_path]
        last_change_b4_time = next(value_change for value_change in reversed(item_value_changes) if (value_change[0] < event_time + sample_cycle*100))
        return last_change_b4_time[1]
    
    def get_signals(self):
        signal_names = [event.signal.rtl_path]
        for item in self.items:
            signal_names.append(item.signal.rtl_path)
        
        return signal_names
    
    def print(self):
        print(self.cover_hash)
