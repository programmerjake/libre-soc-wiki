#!/usr/bin/env python3
import csv
import os
from os.path import dirname, join
from glob import glob
from collections import OrderedDict


def find_wiki_file(name):
    filedir = os.path.dirname(os.path.abspath(__file__))
    tabledir = join(filedir, 'isatables')
    file_path = join(tabledir, name) 
    return file_path

def get_csv(name):
    file_path = find_wiki_file(name)
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def blank_key(row):
    for v in row.items():
        if v:
            return False
    return True

keycolumns = ['in1', 'in2', 'in3', 'out', 'CR in', 'CR out',
                 'ldst len', 'rc', 'lk']
def create_key(row):
    res = OrderedDict()
    #print ("row", row)
    for key in keycolumns:
        # registers
        if key in ['in1', 'in2', 'in3', 'out']:
            if row[key].startswith('R'):
                res[key] = 'R'
            else:
                res[key] = '0'
        # CRs
        if key.startswith('CR'):
            if row[key].startswith('NONE'):
                res[key] = '0'
            else:
                res[key] = '1'
        # LDST len
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

    return res

def dformat(d):
    res = []
    for k, v in d.items():
        res.append("%s: %s" % (k, v))
    return ' '.join(res)

def tformat(d):
    return "|" + ' | '.join(d) + "|"


def process_csvs():
    csvs = {}
    bykey = {}
    primarykeys = set()
    dictkeys = OrderedDict()

    pth = find_wiki_file("*.csv")
    for fname in glob(pth):
        if 'valid' in fname:
            continue
        if 'test' in fname:
            continue
        if 'sprs' in fname:
            continue
        #print (fname)
        csvname = os.path.split(fname)[1]
        csv = get_csv(fname)
        csvs[fname] = csv
        for row in csv:
            if blank_key(row):
                continue
            dkey = create_key(row)
            key = tuple(dkey.values())
            dictkeys[key] = dkey
            primarykeys.add(key)
            if key not in bykey:
                bykey[key] = []
            bykey[key].append((csvname, row['opcode'], row['comment'],
                               row['form'].upper() + '-Form'))

    print ("# keys")
    print ()
    print ('[[!table  data="""')
    print (tformat(keycolumns))
    for key in primarykeys:
        print (tformat(dictkeys[key].values()))
    print ('"""]]')
    print ()

    for key in primarykeys:
        print ("## ", dformat(dictkeys[key]))
        print ()
        for row in bykey[key]:
            print (" * ", row)
        print ()

    bykey = {}
    for fname, csv in csvs.items():
        key

if __name__ == '__main__':
    process_csvs()
