#!/usr/bin/python
import random
import json
import sys
geonameid = 0       # integer id of record in geonames database
name  = 1           #cname of geographical point (utf8) varchar(200)
asciiname = 2       # name of geographical point in plain ascii characters, varchar(200)
alternatenames = 3  # alternatenames, comma separated, ascii names automatically transliterated, convenience attribute from alternatename table, varchar(10000)
latitude = 4        # latitude in decimal degrees (wgs84)
longitude =  5      # longitude in decimal degrees (wgs84)
feature_class = 6   # see http://www.geonames.org/export/codes.html, char(1)
feature_code =  7   # see http://www.geonames.org/export/codes.html, varchar(10)
country_code =  8   # ISO-3166 2-letter country code, 2 characters
cc2 = 9             # alternate country codes, comma separated, ISO-3166 2-letter country code, 200 characters
admin1_code = 10    # fipscode (subject to change to iso code), see exceptions below, see file admin1Codes.txt for display names of this code; varchar(20)
admin2_code = 11    # code for the second administrative division, a county in the US, see file admin2Codes.txt; varchar(80) 
admin3_code = 12    # code for third level administrative division, varchar(20)
admin4_code = 13    # code for fourth level administrative division, varchar(20)
population = 14     # bigint (8 byte int) 
elevation = 15      # in meters, integer
dem = 16            # digital elevation model, srtm3 or gtopo30, average elevation of 3''x3'' (ca 90mx90m) or 30''x30'' (ca 900mx900m) area in meters, integer. srtm processed by cgiar/ciat. 
timezone = 17       # the iana timezone id (see file timeZone.txt) varchar(40)
modification_date = 18 # date of last modification in yyyy-MM-dd format

candidates = []
lines = sys.stdin.readlines()
for line in lines:
     fields = line.split('\t')
     if len(fields) < 19: continue
     if int(fields[population]) > 1000:
     	candidates.append(line)
chosen = set([random.randint(0, len(candidates) - 1) for i in range(1, 10000)])
while (len(chosen ) < 10000):
	x = random.randint(0, len(candidates) - 1)
	if x not in chosen:
		chosen.add(x)
print 'attackers = ['
candidateRecords = []
for candidateIndex in chosen:
	fields = candidates[candidateIndex].split('\t')
	print '{"name": "%s",  "lat": "%s", "lng": "%s"},' % (fields[name], fields[latitude], fields[longitude])
	
print "]"


