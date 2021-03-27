ffrom coverage.regression import Regression
from coverage.covergroups import *

signals_per_test = {'/test1/verilog.fsdb': {
'top.mispredict': [(0, '0'), (272250, '1'), (272350, '0'), (274550, '1'), (274650, '0'), (276950, '1'), (277050, '0'), (299750, '1'), (299850, '0'), (302550, '1'), (302650, '0'), (309250, '1'), (309350, '0'), (311550, '1'), (311650, '0'), (332250, '1'), (332350, '0'), (334550, '1'), (334650, '0'), (441250, '1'), (441350, '0'), (443550, '1'), (443650, '0'), (446350, '1'), (446450, '0'), (458350, '1'), (458450, '0')], 
'top.fault': [(0, 'X'), (272750, '1'), (206050, '1'), (206150, '0'), (221850, '1'), (221950, '0'), (235550, '1'), (235650, '0'), (264350, '1'), (264450, '0'), (306050, '1'), (306150, '0'), (320150, '1'), (320250, '0'), (353650, '1'), (353750, '0'), (373150, '1'), (373250, '0'), (389050, '1'), (389150, '0'), (450950, '1'), (451050, '0'), (480650, '1'), (480750, '0'), (485350, '1'), (485450, '0'), (489950, '1'), (490050, '0'), (522750, '1'), (522850, '0'), (533650, '1'), (533750, '0')], 
'top.snoop': [(0, '0')]}, 
'/test2/verilog.fsdb': 
{'top.mispredict': [(0, '0')], 
'top.fault': [(0, 'X'), (2450, '0')], 
'top.snoop': [(0, '0')]}, 
'/test3/verilog.fsdb': {
'top.mispredict': [(0, '0')], 
'top.fault': [(0, 'X'), (2450, '0')],
'top.snoop': [(0, '0')]}, 
'/test4/verilog.fsdb': 
{'top.mispredict': [(0, '0')], 
'top.fault': [(0, 'X'), (2450, '0')], 
'top.snoop': [(0, '0')]}, 
'/test5/verilog.fsdb': 
{'top.mispredict': [(0, '0')], 
'top.fault': [(0, 'X'), (2450, '0'), (206750, '1'), (206850, '0'), (211650, '1'), (211750, '0')], 
'top.snoop': [(0, '0')]}}


signals_per_test = {'/test1/verilog.fsdb': {
'top.mispredict': [(0, '0'), (272250, '1')], 
'top.fault': [(0, 'X'), (272250, '1')], 
'top.snoop': [(0, '0')]}}

fault_name = 'top.fault'
mispredict_name = 'top.mispredict'
snoop_name = 'top.snoop'


fault_signal = Signal(fault_name, logical_name = "fault")
mispredict_signal = Signal(mispredict_name, logical_name = "mispredict")
snoop_signal = Signal(snoop_name, logical_name = "snoop")

# define the event we want to sample our coverage on
fault_event = Event(fault_signal, [1])

# define the signals we want to sample upon the event, along with relative time on which they should be sampled
mispredict_item = CoverItem(mispredict_signal, buckets=range(-2,3), buckets_type=BucketType.time)
snoop_item = CoverItem(snoop_signal, buckets=range(-2,3), buckets_type=BucketType.time)
mispredict_X_snoop = Cross([mispredict_item, snoop_item])

# link the event and item together
collisions_at_fault = Cover(event=fault_event, items=[mispredict_item,snoop_item], crosses=[mispredict_X_snoop])

regression = Regression("./")
regression.signals_per_test = signals_per_test

regression.extract_cov([collisions_at_fault])

collisions_at_fault.print()