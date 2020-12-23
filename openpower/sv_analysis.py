#!/usr/bin/env python2
#
# NOTE that this program is python2 compatible, please do not stop it
# from working by adding syntax that prevents that.
#
# Initial version written by lkcl Oct 2020
# This program analyses the Power 9 op codes and looks at in/out register uses
# The results are displayed:
#	https://libre-soc.org/openpower/opcode_regs_deduped/
#
# It finds .csv files in the directory isatables/
# then goes through the categories and creates svp64 CSV augmentation
# tables on a per-opcode basis

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

# Write an array of dictionaries to the CSV file name:
def write_csv(name, items, headers):
    file_path = find_wiki_file(name)
    with open(file_path, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writeheader()
        writer.writerows(items)

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

tablecols = ['unit', 'in', 'outcnt', 'CR in', 'CR out', 'imm'
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
            if row['comment'].startswith('cr'):
                res['crop'] = '1'
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


    # constants
    if row['in2'].startswith('CONST_'):
        res['imm'] = "1" # row['in2'].split("_")[1]
    else:
        res['imm'] = ''

    return res

#
def dformat(d):
    res = []
    for k, v in d.items():
        res.append("%s: %s" % (k, v))
    return ' '.join(res)

def tformat(d):
    return ' | '.join(d) + " |"

def keyname(row):
    res = []
    if row['unit'] != 'OTHER':
        res.append(row['unit'])
    if row['in'] != '0':
        res.append('%sR' % row['in'])
    if row['outcnt'] != '0':
        res.append('%sW' % row['outcnt'])
    if row['CR in'] == '1' and row['CR out'] == '1':
        if 'crop' in row:
            res.append("CR=2R1W")
        else:
            res.append("CRio")
    elif row['CR in'] == '1':
        res.append("CRi")
    elif row['CR out'] == '1':
        res.append("CRo")
    elif 'imm' in row and row['imm']:
        res.append("imm")
    return '-'.join(res)


def process_csvs():
    csvs = {}
    bykey = {}
    primarykeys = set()
    dictkeys = OrderedDict()
    immediates = {}
    insns = {} # dictionary of CSV row, by instruction

    print ("# OpenPOWER ISA register 'profile's")
    print ('')
    print ("this page is auto-generated, do not edit")
    print ("created by http://libre-soc.org/openpower/sv_analysis.py")
    print ('')

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
            insns[row['comment']] = row # accumulate csv data by instruction
            dkey = create_key(row)
            key = tuple(dkey.values())
            # print("key=", key)
            dictkeys[key] = dkey
            primarykeys.add(key)
            if key not in bykey:
                bykey[key] = []
            bykey[key].append((csvname, row['opcode'], row['comment'],
                               row['form'].upper() + '-Form'))

            # detect immediates, collate them (useful info)
            if row['in2'].startswith('CONST_'):
                imm = row['in2'].split("_")[1]
                if key not in immediates:
                    immediates[key] = set()
                immediates[key].add(imm)

    primarykeys = list(primarykeys)
    primarykeys.sort()

    # mapping to old SVPrefix "Forms"
    mapsto = {'3R-1W-CRio': 'RM-1P-3S1D',
              '2R-1W-CRio': 'RM-1P-2S1D',
              '2R-1W-CRi': 'RM-1P-3S1D',
              '2R-1W-CRo': 'RM-1P-2S1D',
              '2R': 'non-SV',
              '2R-1W': 'RM-1P-2S1D',
              '1R-CRio': 'RM-2P-2S1D',
              '2R-CRio': 'RM-1P-2S1D',
              '2R-CRo': 'RM-1P-2S1D',
              '1R': 'non-SV',
              '1R-1W-CRio': 'RM-2P-1S1D',
              '1R-1W-CRo': 'RM-2P-1S1D',
              '1R-1W': 'RM-2P-1S1D',
              '1R-1W-imm': 'RM-2P-1S1D',
              '1R-CRo': 'RM-2P-1S1D',
              '1R-imm': 'non-SV',
              '1W': 'non-SV',
              '1W-CRi': 'RM-2P-1S1D',
              'CRio': 'RM-2P-1S1D',
              'CR=2R1W': 'RM-1P-2S1D',
              'CRi': 'non-SV',
              'imm': 'non-SV',
              '': 'non-SV',
              'LDST-2R-imm': 'LDSTRM-2P-2S',
              'LDST-2R-1W-imm': 'LDSTRM-2P-2S1D',
              'LDST-2R-1W': 'LDSTRM-2P-2S1D',
              'LDST-2R-2W': 'LDSTRM-2P-2S1D',
              'LDST-1R-1W-imm': 'LDSTRM-2P-1S1D',
              'LDST-1R-2W-imm': 'LDSTRM-2P-1S2D',
              'LDST-3R': 'LDSTRM-2P-3S',
              'LDST-3R-CRo': 'LDSTRM-2P-3S',  # st*x
              'LDST-3R-1W': 'LDSTRM-2P-2S1D',  # st*x
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
    print (tformat(tablecols) + " imms | name |")

    # print out the keys and the table from which they're derived
    for key in primarykeys:
        name = keyname(dictkeys[key])
        row = tformat(dictkeys[key].values())
        imms = list(immediates.get(key, ""))
        imms.sort()
        row += " %s | " % ("/".join(imms))
        row += " %s |" % name
        print (row)
    print ('"""]]')
    print ('')

    # print out, by remap name, all the instructions under that category
    for key in primarykeys:
        name = keyname(dictkeys[key])
        value = mapsto.get(name, "-")
        print ("## %s (%s)" % (name, value))
        print ('')
        print ('[[!table  data="""')
        print (tformat(['CSV', 'opcode', 'asm', 'form']))
        rows = bykey[key]
        rows.sort()
        for row in rows:
            print (tformat(row))
        print ('"""]]')
        print ('')

    #for fname, csv in csvs.items():
    #    print (fname)

    #for insn, row in insns.items():
    #    print (insn, row)

    print ("# svp64 remaps")
    svp64 = OrderedDict()
    # create a CSV file, per category, with SV "augmentation" info
    csvcols = ['insn', 'Ptype', 'Etype', '0', '1', '2', '3']
    for key in primarykeys:
        # get the decoded key containing row-analysis, and name/value
        dkey = dictkeys[key]
        name = keyname(dkey)
        value = mapsto.get(name, "-")
        if value == 'non-SV':
            continue

        # store csv entries by svp64 RM category
        if value not in svp64:
            svp64[value] = []

        # print out svp64 tables by category
        print ("## %s (%s)" % (name, value))
        print ('')
        print ('[[!table  data="""')
        print (tformat(csvcols))
        rows = bykey[key]
        rows.sort()

        for row in rows:
            # get the instruction
            insn_name = row[2]
            insn = insns[insn_name]
            # start constructing svp64 CSV row
            res = OrderedDict()
            res['insn'] = insn_name
            res['Ptype'] = value.split('-')[1] # predication type (RM-xN-xxx)
            # get whether R_xxx_EXTRAn fields are 2-bit or 3-bit
            res['Etype'] = 'EXTRA2'
            # go through each register matching to Rxxxx_EXTRAx
            for k in ['0', '1', '2', '3']:
                res[k] = ''
    
            # temporary useful info
            for k in ['in1', 'in2', 'in3', 'out', 'CR in', 'CR out']:
                if insn[k].startswith('CONST'):
                    res[k] = ''
                else:
                    res[k] = insn[k]

            # sigh now the fun begins.  this isn't the sanest way to do it
            # but the patterns are pretty regular.
            if value == 'LDSTRM-2P-1S1D':
                res['Etype'] = 'EXTRA3' # RM EXTRA3 type
                res['0'] = 'd:RT' # RT: Rdest_EXTRA3
                res['1'] = 's:RA' # RA: Rsrc1_EXTRA3

            elif value == 'LDSTRM-2P-1S2D':
                res['Etype'] = 'EXTRA2' # RM EXTRA2 type
                res['0'] = 'd:RT' # RT: Rdest1_EXTRA2
                res['1'] = 's:RA' # RA: Rsrc1_EXTRA2
                res['2'] = 'd:RA' # RA: Rdest2_EXTRA2

            elif value == 'LDSTRM-2P-2S':
                res['Etype'] = 'EXTRA3' # RM EXTRA2 type
                res['0'] = 'd:RS' # RT: Rdest1_EXTRA2
                res['1'] = 's:RA' # RA: Rsrc1_EXTRA2

            elif value == 'LDSTRM-2P-2S1D':
                if 'st' in insn and 'x' not in insn: # stwu/stbu etc
                    res['Etype'] = 'EXTRA2' # RM EXTRA2 type
                    res['0'] = 'd:RS' # RS: Rdest1_EXTRA2
                    res['1'] = 'd:RA' # RA: Rdest2_EXTRA2
                    res['2'] = 's:RA' # RA: Rsrc1_EXTRA2
                if 'st' in insn and 'x' in insn: # stwux
                    res['Etype'] = 'EXTRA2' # RM EXTRA2 type
                    res['0'] = 'd:RS' # RS: Rdest1_EXTRA2
                    res['1'] = 'd:RA' # RA: Rdest2_EXTRA2, RA: Rsrc1_EXTRA2
                    res['2'] = 's:RB' # RB: Rsrc2_EXTRA2
                elif 'u' in insn: # ldux etc.
                    res['Etype'] = 'EXTRA2' # RM EXTRA2 type
                    res['0'] = 'd:RT' # RT: Rdest1_EXTRA2
                    res['1'] = 'd:RA' # RA: Rdest2_EXTRA2
                    res['2'] = 's:RB' # RB: Rsrc1_EXTRA2
                else:
                    res['Etype'] = 'EXTRA2' # RM EXTRA2 type
                    res['d0'] = 'RT' # RT: Rdest1_EXTRA2
                    res['s1'] = 'RA' # RA: Rsrc1_EXTRA2
                    res['s2'] = 'RB' # RB: Rsrc2_EXTRA2

            elif value == 'LDSTRM-2P-3S':
                res['Etype'] = 'EXTRA2' # RM EXTRA2 type
                res['0'] = 's:RS,d:CR0' # RS: Rsrc1_EXTRA2 CR0: dest
                res['1'] = 's:RA' # RA: Rsrc2_EXTRA2
                res['2'] = 's:RB' # RA: Rsrc3_EXTRA2

            elif value == 'RM-2P-1S1D':
                res['Etype'] = 'EXTRA3' # RM EXTRA3 type
                if key == 'CRio' and insn == 'mcrf':
                    res['0'] = 'd:BF' # BFA: Rdest1_EXTRA3
                    res['1'] = 's:BFA' # BFA: Rsrc1_EXTRA3
                elif insn == 'setb':
                    res['0'] = 'd:RT' # RT: Rdest1_EXTRA3
                    res['1'] = 's:BFA' # BFA: Rsrc1_EXTRA3
                elif insn_name.startswith('cmp'): # cmpi
                    res['0'] = 'd:BF' # BF: Rdest1_EXTRA3
                    res['1'] = 's:RA' # RA: Rsrc1_EXTRA3
                else:
                    res['0'] = 'TODO'

            elif value == 'RM-1P-2S1D':
                res['Etype'] = 'EXTRA3' # RM EXTRA3 type
                if insn_name.startswith('cr'):
                    res['0'] = 'd:BT' # BT: Rdest1_EXTRA3
                    res['1'] = 's:BA' # BA: Rsrc1_EXTRA3
                    res['2'] = 's:BB' # BB: Rsrc2_EXTRA3
                elif insn_name.startswith('cmp'): # cmp
                    res['0'] = 'd:BF' # BF: Rdest1_EXTRA3
                    res['1'] = 's:RA' # RA: Rsrc1_EXTRA3
                    res['2'] = 's:RB' # RB: Rsrc1_EXTRA3
                else:
                    res['0'] = 'TODO'

            elif value == 'RM-2P-2S1D':
                res['Etype'] = 'EXTRA2' # RM EXTRA2 type
                if insn_name.startswith('mt'): # mtcrf
                    res['0'] = 'd:CR' # CR: Rdest1_EXTRA2
                    res['1'] = 's:RS' # RS: Rsrc1_EXTRA2
                    res['2'] = 's:CR' # CR: Rsrc2_EXTRA2
                else:
                    res['0'] = 'TODO'

            # print out the row
            print (tformat(res.values()))
            # add to svp64 csvs
            svp64[value].append(res)

        print ('"""]]')
        print ('')

if __name__ == '__main__':
    process_csvs()
