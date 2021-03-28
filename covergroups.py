import itertools
from enum import Enum
import pandas as pd


class BucketType(Enum):
    value = 1
    time = 2

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


class CoverBase:
    def __init__(self):
        pass

    def get_value_at(self, dataset, rtl_path, event_time, sample_cycle):
        item_value_changes = dataset[rtl_path]
        last_change_b4_time = next(value_change for value_change in reversed(item_value_changes) if (value_change[0] < event_time + sample_cycle*100))
        return last_change_b4_time[1]
        
class CoverItem(CoverBase):
    # signal : Signal
    # sample_cycles : cycles from event
    def __init__(self, signal, buckets, buckets_type=BucketType.value):
        self.signal = signal
        self.buckets = buckets
        self.buckets_type = buckets_type

        self.create_empty()

    def create_empty(self):
        item_table = []

        for bucket in self.buckets:
            item_table.append([bucket, False])

        self.item_df = pd.DataFrame(item_table)
        self.item_df.columns = [self.signal.logical_name, 'covered']

    def sample(self, dataset, event_time):
        if self.buckets_type == BucketType.time:
            for sample_cycle in self.buckets:
                value = self.get_value_at(dataset, self.signal.rtl_path, event_time, sample_cycle)
                if value == str(1):
                    self.item_df.loc[self.item_df[self.signal.logical_name]==sample_cycle, [
                        'covered']] = True

class Cross(CoverBase):
    def __init__(self, items):
        self.items = items
        self.name = '_X_'.join([item.signal.logical_name for item in items])
        self.create_empty()

    def create_empty(self):

        cross_item_table = []

        cross_item_table_header = [item.signal.logical_name for item in self.items]
        cross_item_table_header.append('covered')
            
        cross_items_buckets = []    
        for item in self.items:
            cross_items_buckets.append(item.buckets)
            
        for cross_bucket in list(itertools.product(*cross_items_buckets)):
            #cross_bucket_name = ','.join(cross_bucket)
            cross_item_table_row = [bucket for bucket in cross_bucket]
            cross_item_table_row.append(False)

            cross_item_table.append(cross_item_table_row)

        self.cross_item_df = pd.DataFrame(cross_item_table)
        self.cross_item_df.columns = cross_item_table_header

    def sample(self, dataset, event_time):

        cross_item_table = [];

        cross_items_bucket_values = []
        for item in self.items:
            if item.buckets_type == BucketType.time:
                bucket_values = []
                for sample_cycle in item.buckets:
                    value = self.get_value_at(dataset, item.signal.rtl_path, event_time, sample_cycle)
                    bucket_values.append((item.signal.logical_name, sample_cycle, (value == str(1))))
                cross_items_bucket_values.append(bucket_values)

        for cross_bucket_value in list(itertools.product(*cross_items_bucket_values)):
            if all([hit[2] for hit in cross_bucket_value]):
                print("found a hit: ", cross_bucket_value)
                for index,row in self.cross_item_df.iterrows():
                    if self.is_row_matching_values(row, cross_bucket_value):
                        self.cross_item_df.loc[index, 'covered'] = True;

        if len(cross_item_table) > 0:
            self.cross_item_table.extend(cross_item_table)

    def is_row_matching_values(self, df_row, row_values):
        match = True
        for value in row_values:
            if df_row[value[0]] != value[1]:
                match = False

        return match
    
class Cover:
    # event: Event
    # items : list of CoverItem
    # crosses : list of list of CoverItem
    def __init__(self,event,items,crosses):
        self.event = event
        self.items = items
        self.crosses = crosses
        
       
    def sample(self, dataset, event_time):
        for item in self.items:
            item.sample(dataset, event_time)

        for cross in self.crosses:
            cross.sample(dataset, event_time)
                    
    def get_signals(self):
        signal_names = [event.signal.rtl_path]
        for item in self.items:
            signal_names.append(item.signal.rtl_path)
        
        return signal_names
    
    def print(self):
        for item in self.items:
            print(item.item_df)
        for cross in self.crosses:
            print(cross.cross_item_df)
