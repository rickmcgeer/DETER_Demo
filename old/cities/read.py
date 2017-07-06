f = open('cities.txt', 'r')
lines = f.readlines()
f.close()
for line in lines:
    fields = line.split('\t')
    cc = fields[8]
    if cc in set(['US', 'MX', 'CA']): print line
