#!/usr/bin/python
import datetime
import sys
import os
import json
execfile('searchBase64DB.py')
from config import port
import math
import uuid

from flask import Flask
from flask import request
from flask.ext.cors import CORS, cross_origin
from loadManager import DataManager

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Code to support the cities app -- add-on, not part of the main distribution

def getLatLng(lngLatList):
    return {"lng": float(lngLatList[0]), "lat":float(lngLatList[1])}

# latLngDistance.  Assumes a rectangular grid, and so it's bogus, but it's a lot cheaper than computing the great circle distance,,,
# actually returns the square
def latLngDistance(latLng1, latLng2):
    latDist = latLng2['lat'] - latLng1['lat']
    latDist *= latDist
    lngDist = latLng2['lng'] - latLng1['lng']
    lngDist *= lngDist
    return latDist + lngDist


def genericRecord(aRecord):
    return {'name': aRecord['name'], 'id': aRecord['_id']['$oid']}

# defaultIcon = 'http://maps.google.com/mapfiles/ms/icons/blue.png'
defaultIcon = 'https://raw.githubusercontent.com/m-hemmings/MiscFiles/master/GoogleIcons/blue_MarkerI.png'

def getIcon(aNode):
    if not 'icon' in aNode: return defaultIcon
    if aNode['icon'] == 'None': return defaultIcon
    return aNode['icon']

def nodeRecord(node):
    record = getLatLng(node['coordinates'])
    record['icon'] = getIcon(node)
    record['id'] = node['_id']['$oid']
    record['name'] = node['name']
    record['rotation'] = node['rotate']
    if 'icon-coords' in node:
        record['icon-coords'] = getLatLng(node['icon-coords'])
    return record

def hopRecord(aHop):
    record = genericRecord(aHop)
    record['weight'] =  1
    record['start'] = getLatLng(aHop['scoord'])
    record['end'] = getLatLng(aHop['dcoord'])
    return record



def eventRecord(anEvent):
    record = {'id': anEvent['_id']['$oid']}
    record['ts'] = anEvent['ts']
    record['type'] = anEvent['type']
    if (record['type'] == 'attack_path'):
        record['path'] = [getLatLng(coordPair) for coordPair in anEvent['path_coord']]
    elif (record['type'] == 'host_health'):
        record['host'] = getLatLng(anEvent['host'])
        record['health'] = anEvent['health']
    elif (record['type'] in set('monitor_start', 'monitor_stop', 'monitor_indicator')):
        record['host_name'] = anEvent['host_name']
        record['host_id'] = anEvent['host_id']

    return record

sys.path.append('./cities')

def positionEqual(r1, r2):
    return r1['lat'] == r2['lat'] and r1['lng'] == r2['lng']



citiesData = {}

def cmpLngLat(ll1, ll2):
    l1 = ll1['lat'] - ll2['lat']
    l2 = ll1['lng'] - ll2['lng']
    if (l1 == 0 and l2 == 0): return 0
    if (l1 > 0): return 1
    if (l1 < 0): return -1
    if (l2 < 0): return -1
    return 1

def cmpPos(health1, health2):
    return cmpLngLat(health1['host'], health2['host'])

#
# calls.  reload the DB
#
@app.route('/reload')
def reload():
    from data import hops, mapevents, nodes
    citiesData['nodes'] = [nodeRecord(node) for node in nodes]
    citiesData['hops'] = [hopRecord(hop) for hop in hops]
    citiesData['mapevents'] = [eventRecord(anEvent) for anEvent in mapevents]
    healths = [record for record in citiesData['mapevents'] if record['type'] == 'host_health']
    healths.sort(cmp = cmpPos)
    lngLat = healths[0]['host']
    healths[0]['host_id'] = 'added_host0'
    count = 0
    for health in healths[1:]:
        if cmpLngLat(health['host'], lngLat) != 0:
            lngLat = health['host']
            count += 1
        health['host_id'] = 'added_host%d' % count

    return 'Done!'

#
# calls.  reload the DB
#
@app.route('/load_debug')
def reloadDebug():
    from data import hops, mapevents, nodes
    citiesData['nodes'] = [nodeRecord(node) for node in nodes]
    citiesData['hops'] = [hopRecord(hop) for hop in hops]
    citiesData['mapevents'] = [eventRecord(anEvent) for anEvent in mapevents]
    sort(citiesData['mapevents'], key=lambda event: event['ts'])
    return json.dumps({'hops': hops, 'mapevents':mapevents, 'nodes':nodes, 'citiesData': citiesData})



# reload on initialization
reload()

#
# calls
#
@app.route('/backbone')
def getBackbone():
    return json.dumps(citiesData['hops'])

@app.route('/nodes')
def getNodes():
    return json.dumps(citiesData['nodes'])

@app.route('/events')
def getEvents():
    return json.dumps(citiesData['mapevents'])

# -- end new cities code --



dataManager = DataManager()

#
# Dig out a  field, convert it using convertFunction, and check the result
# using checkFunction.  convertFunction should be something which takes a string
# and returns the right type, throwing a ValueError if there is a problem.  checkFunction
# takes a single parameter and returns True if it's valid, False otherwise.  Annotates
# requestResult either with the  value or with the error message if there is one.  This
# is designed to be called multiple times with the same requestResult, so error, once
# set to True, should never be set to False.
#


def getField(request, requestResult, fieldName, convertFunction, checkFunction):
    value = request.args.get(fieldName)
    if (not value):
        requestResult['error'] = True
        requestResult['message'] += 'fieldName %s missing.  ' % fieldName
    try:
        val = convertFunction(value)
        if (checkFunction(val)):
            requestResult[fieldName] = val
        else:
            requestResult['error'] = True
            requestResult['message'] += 'validity check failed for field %s, value %s' % (fieldName, value)
    except (ValueError, TypeError):
        requestResult['error'] = True
        requestResult['message'] += 'conversion function failed for fieldName %s, not %s.  ' % (fieldName, value)

#
# Parse a request and return the result.  The specifications
# are the fields, so all this does is iterate over the fields
# provided as arguments
#
def parseRequest(request, fields):
    result = {'error': False, 'message': ''}
    for (fieldName, conversion, checkFunction) in fields:
        getField(request, result, fieldName, conversion, checkFunction)
    return result

basicParseFields = [('year', int, lambda x: x in range(1997, 2016)),
          ('month', int, lambda x: x in range(1, 13)),
          ('res', int, lambda x: x in [1, 2, 4, 10])
          ]

fullParseFields = basicParseFields + [
        ('nwLat', float, lambda x: x <= 90.0 and x >= -90.0),
        ('seLat', float, lambda x: x <= 90.0 and x >= -90.0),
        ('nwLon', float, lambda x: x <= 180.0 and x >= -180.0),
        ('seLon', float, lambda x: x <= 180.0 and x >= -180.0),
    ]

#
#  Turn a structure into a string
#

@app.route('/test')
def test_basic():
    result = parseRequest(request, basicParseFields)
    if result['error']:
        return 'Error in request ' + result['message']
    else:
        return json.dumps(result)

@app.route('/test_full')
def test_full():
    result = parseRequest(request, fullParseFields)
    if result['error']:
        return 'Error in request ' + result['message']
    else:
        return json.dumps(result)

def parseAndCheck(request):
    query = parseRequest(request, fullParseFields)
    if query['error']:
        query['message'] = 'Error in request ' + query['message']
        return query
    if (not dataManager.checkLoadable(query['year'], query['month'], query['res'])):
        query['error'] = True
        query['message'] = "Dataset %s is not loaded" % convertToString(query['year'], query['month'], query['res'])
    else:
        query['error'] = False
    return query

degreeFields = ['nwLat', 'nwLon', 'seLat', 'seLon']

def dumpQuery(query):
    str = ['query[%s] = %s' % (key, query[key]) for key in query]
    print ', '.join(str)
    sys.stdout.flush()


def convertDegreesToTenthsOfDegrees(query, fields):
    for field in fields:
        query[field] = int(math.floor(query[field] * 10))

@app.route('/get_time')
def get_times():
    query = parseAndCheck(request)
    if (query['error']):
        return query['message']
    convertDegreesToTenthsOfDegrees(query, degreeFields)
    stats = getStats(dataManager, query['year'], query['month'], query['res'],
               query['nwLat'], query['seLat'], query['nwLon'], query['seLon'])
    return json.dumps(stats)

@app.route('/show_inventory')
def get_inventory():
    loadable = '\n'.join(["year = %d, month=%d, res=%d" % tuple for tuple in dataManager.getLoadableKeys()])
    print loadable
    inventory = '\n'.join(join(["year = %d, month=%d, res=%d" % tuple for tuple in dataManager.getAllLoadedKeys()]))
    print inventory
    size = '\nTotal Bytes loaded: %dMB\n' % int(round(dataManager.getSize()/1.0E6))
    print size
    return loadable + '\nData sets loaded\n' + inventory + size

@app.route('/get_data')
def get_data():
    query = parseAndCheck(request)
    if (query['error']):
        return query['message']
    convertDegreesToTenthsOfDegrees(query, degreeFields)
    result = searchDB(dataManager, query['year'], query['month'], query['res'],
               query['nwLat'], query['seLat'], query['nwLon'], query['seLon'])
    return json.dumps({
        'sw': result['swCorner'], 'ptsPerRow': result['pointsPerRow'],
        'ptsPerDegree': result['pointsPerDegree'], 'base64String': result['base64String']
    })


@app.route('/get_data_readable')
def get_data_readable():
    query = parseAndCheck(request)
    if (query['error']):
        return query['message']
    convertDegreesToTenthsOfDegrees(query, degreeFields)
    result = searchDBReturnRows(dataManager, query['year'], query['month'], query['res'],
               query['nwLat'], query['seLat'], query['nwLon'], query['seLon'], False)
    return json.dumps({
        'sw': result['swCorner'], 'ptsPerRow': result['pointsPerRow'],
        'ptsPerDegree': result['pointsPerDegree'], 'base64String': '\n'.join(result['sequences'])
    })

@app.route('/get_data_rectangle')
def get_data_rectangle():
    query = parseAndCheck(request)
    if (query['error']):
        return query['message']
    convertDegreesToTenthsOfDegrees(query, degreeFields)
    searchResult = searchDBReturnRows(dataManager, query['year'], query['month'], query['res'],
               query['nwLat'], query['seLat'], query['nwLon'], query['seLon'], False)
    indicesOnly = 'indicesOnly' in request.args
    result = convertToRectangles(searchResult, 'indicesOnly')
    return json.dumps({
        'sw': searchResult['swCorner'],
        'ptsPerDegree': searchResult['pointsPerDegree'], 'rectangles': ','.join(result)
    })

@app.route('/help')
def print_help():
    str = '<p>/show_inventory: print loaded data'
    str += '<p>/get_data?&lt;args&gt;:get the data as a base-64 string with metadata.  See below for argument format'
    str += '<p>/get_data_readable?&lt;args&gt;:same as get_data but put the base64 string into rows for human readability'
    str += '<p>/get_times?&lt;args&gt;: get the statistics on the query'
    str += '<p>/get_data_rectangle?&lt;args&gt;: get the data as a set of 5-tuple rectangles rather than as a set of strings.  In addition to'
    str += ' the usual args, if indicesOnly is given as an argument, gives row/column indices rather than lat/lon for coordinates'
    str += '<p>/help: print this message\n'
    str += '&lt;args&gt;: seLon=&lt;longitude&gt;, nwLon=&lt;longitude&gt;, seLat=&lt;latitude&gt;, nwLat=&lt;latitude&gt;,'
    str += 'year=&lt;year&gt;, month=&lt;1-12&gt;, res=&lt;1,2,4, or 10&gt;'
    return str

@app.route('/')
def index():
   return print_help()

if __name__ == '__main__':
    # for fileName in yearFiles:
    #     execfile(fileName)
    # print memory()
    # app.debug = True

    dataManager.checkExistenceSanityCheck()
    app.run(host='0.0.0.0', port=port)
