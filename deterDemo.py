#!/usr/bin/python
import datetime
import sys
import os
import json
import math
import uuid

sys.path.append('cities')

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
edgeIcon = 'http://icons.veryicon.com/png/Internet%20%26%20Web/Round%20Edge%20Social/cloud%20app.png'

def getIcon(aNode):
    if not 'icon' in aNode: return defaultIcon
    if aNode['icon'] == 'None': return defaultIcon
    if aNode['icon'] == 'edge-icon.svg': return edgeIcon
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
    elif (record['type'] in set(['monitor_start', 'monitor_stop', 'monitor_indicator'])):
        record['host'] = getLatLng(anEvent['host'])
        if record['type'] == 'monitor_indicator':
            record['target'] = getLatLng(anEvent['target'])
    return record


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

# load the db

def loadBody(nodes, hops, mapevents):
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
    monitors = [record for record in citiesData['mapevents'] if record['type'] in set(['monitor_start', 'monitor_stop', 'monitor_indicator'])]
    for monitor in monitors:
        for node in citiesData['nodes']:
            if (cmpLngLat(node, monitor['host'])):
                monitor['host_name'] = node['name']
                monitor['host_id'] = node['id']
    citiesData['mapevents'].sort(key=lambda event: event['ts'])


