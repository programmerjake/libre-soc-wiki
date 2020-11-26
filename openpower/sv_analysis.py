#!/usr/bin/env python3
# Initial version written by lkcl Oct 2020
# This program analyses the Power 9 op codes and looks at in/out register uses
# The results are displayed:
#	https://libre-soc.org/openpower/opcode_regs_deduped/
#
# It finds .csv files in the directory isatables/

import csv
import os
from os.path import dirname, join
from glob import glob
from collections import OrderedDict

# Return absolute path (ie $PWD) + isatables + name
def find_wiki_file(name):
    filedir = os.path.dirname(os.path.abspath(__file__))
    tabledir = join(filedir, 'isatables')
    file_path = join(tabledir, name) 
    return file_path

# Return an array of dictionaries from the CSV file name:
def get_csv(name):
    file_path = find_wiki_file(name)
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

# This will return True if all values are true.
# Not sure what this is about
def blank_key(row):
    #for v in row.values():
    #    if 'SPR' in v: # skip all SPRs
    #        return True
    for v in row.values():
        if v:
            return False
    return True

# General purpose registers have names like: RA, RT, R1, ...
# Floating point registers names like: FRT, FRA, FR1, ..., FRTp, ...
# Return True if field is a register
def isreg(field):
    return field.startswith('R') or field.startswith('FR')


# These are the attributes of the instructions,
# register names
keycolumns = ['unit', 'in1', 'in2', 'in3', 'out', 'CR in', 'CR out',
                 ] # don't think we need these: 'ldst len', 'rc', 'lk']

tablecols = ['unit', 'in', 'outcnt', 'CR in', 'CR out', 
                 ] # don't think we need these: 'ldst len', 'rc', 'lk']

def create_key(row):
    res = OrderedDict()
    #print ("row", row)
    for key in keycolumns:
        # registers IN - special-case: count number of regs RA/RB/RC/RS
        if key in ['in1', 'in2', 'in3']:
            if 'in' not in res:
                res['in'] = 0
            if isreg(row[key]):
                res['in'] += 1

        # registers OUT
        if key == 'out':
            # If upd is 1 then increment the count of outputs
            if 'outcnt' not in res:
                res['outcnt'] = 0
            if isreg(row[key]):
                res['outcnt'] += 1
            if row['upd'] == '1':
                res['outcnt'] += 1

        # CRs (Condition Register) (CR0 .. CR7)
        if key.startswith('CR'):
            if row[key].startswith('NONE'):
                res[key] = '0'
            else:
                res[key] = '1'
        # unit
        if key == 'unit':
            if row[key] == 'LDST': # we care about LDST units
                res[key] = row[key]
            else:
                res[key] = 'OTHER'
        # LDST len (LoadStore length)
        if key.startswith('ldst'):
            if row[key].startswith('NONE'):
                res[key] = '0'
            else:
                res[key] = '1'
        # rc, lk
        if key in ['rc', 'lk']:
            if row[key] == 'ONE':
                res[key] = '1'
            elif row[key] == 'NONE':
                res[key] = '0'
            else:
                res[key] = 'R'
        if key == 'lk':
            res[key] = row[key]

    # Convert the numerics 'in' & 'outcnt' to strings
    res['in'] = str(res['in'])
    res['outcnt'] = str(res['outcnt'])

    return res

#
def dformat(d):
    res = []
    for k, v in d.items():
        res.append("%s: %s" % (k, v))
    return ' '.join(res)

def tformat(d):
    return ' | '.join(d) + "|"

def keyname(row):
    res = []
    if row['unit'] != 'OTHER':
        res.append(row['unit'])
    if row['in'] != '0':
        res.append('%sR' % row['in'])
    if row['outcnt'] != '0':
        res.append('%sW' % row['outcnt'])
    if row['CR in'] == '1' and row['CR out'] == '1':
        res.append("CRio")
    elif row['CR in'] == '1':
        res.append("CRi")
    elif row['CR out'] == '1':
        res.append("CRo")
    return '-'.join(res)


def process_csvs():
    csvs = {}
    bykey = {}
    primarykeys = set()
    dictkeys = OrderedDict()

    # Expand that (all .csv files)
    pth = find_wiki_file("*.csv")

    # Ignore those containing: valid test sprs
    for fname in glob(pth):
        if 'valid' in fname:
            continue
        if 'test' in fname:
            continue
        if 'sprs' in fname:
            continue

        #print (fname)
        csvname = os.path.split(fname)[1]
        # csvname is something like: minor_59.csv, fname the whole path
        csv = get_csv(fname)
        csvs[fname] = csv
        for row in csv:
            if blank_key(row):
                continue
            dkey = create_key(row)
            key = tuple(dkey.values())
            # print("key=", key)
            dictkeys[key] = dkey
            primarykeys.add(key)
            if key not in bykey:
                bykey[key] = []
            bykey[key].append((csvname, row['opcode'], row['comment'],
                               row['form'].upper() + '-Form'))

    primarykeys = list(primarykeys)
    primarykeys.sort()

    # mapping to old SVPrefix "Forms"
    mapsto = {'3R-1W-CRio': 'FR4',
              '2R-1W-CRio': 'R',
              '2R-1W-CRi': 'R',
              '2R-1W-CRo': 'R',
              '2R-1W': 'R',
              '2R-CRio': 'R',
              '2R-CRo': 'R',
              '1R-1W-CRio': 'R',
              '1R-1W-CRo': 'R',
              '1R-1W': 'R',
              '1R-1W': 'R',
              }
    print ("# map to old SV Prefix")
    print ('')
    print ('[[!table  data="""')
    for key in primarykeys:
        name = keyname(dictkeys[key])
        value = mapsto.get(name, "-")
        print (tformat([name, value+ " "]))
    print ('"""]]')
    print ('')

    print ("# keys")
    print ('')
    print ('[[!table  data="""')
    print (tformat(tablecols) + " name |")

    for key in primarykeys:
        name = keyname(dictkeys[key])
        print (tformat(dictkeys[key].values()) + " %s |" % name)
    print ('"""]]')
    print ('')

    for key in primarykeys:
        name = keyname(dictkeys[key])
        print ("## %s " % name)
        print ('')
        print ('[[!table  data="""')
        print (tformat(['CSV', 'opcode', 'asm', 'form']))
        rows = bykey[key]
        rows.sort()
        for row in rows:
            print (tformat(row))
        print ('"""]]')
        print ('')

    bykey = {}
    for fname, csv in csvs.items():
        key

if __name__ == '__main__':
    process_csvs()
