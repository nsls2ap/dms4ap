import json
import random


import cothread.catools as ca

pvvals = json.load(open("pv_vals.txt"))

pvs = []
vals = []
for k, v in pvvals.iteritems():
    pvs.append(k)
    if v == 0.0:
        vals.append(random.uniform(0.1, 1.0))
    else:
        vals.append(v)

ca.caput(pvs, vals)