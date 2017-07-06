#!/usr/bin/python
import sys
lines = sys.stdin.readlines()
for line in lines:
    fields = line.split('\t')
    print len(fields)

