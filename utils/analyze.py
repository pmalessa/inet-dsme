#!/usr/bin/env python

import argparse
import sys
import os
import csv
import glob
from subprocess import *
import numpy as np
import scipy as sp
import scipy.stats
from Run import Run
import ConfigParser
from sets import Set

def mean_confidence_interval(data, confidence=0.95):
    a = 1.0*np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * sp.stats.t._ppf((1+confidence)/2., n-1)
    return m, h

def main(args):
    measures = ['minPRR','meanPRR','maxDelay','meanDelay']

    allhosts = set()
    aggregated = {}
    runs = []
    repetitions = Set()
    for f in glob.glob(args.results+'/*.sca'):
        r = Run()
        r.load(f)

        allhosts.update(r.hosts.keys())

        runs.append(r)
        
        repetitions.add(r.param["seedset"])
        for m in measures:
            aggregated.setdefault(r.param["configname"],{}).setdefault(r.param["sendInt"],{}).setdefault(m,{})[r.param["seedset"]] = r.measure[m]

    with open(args.results+'/aggregated.csv','w') as resultfile:
        cols = ['config','sendInt']
        for m in measures:
            cols += [m, m+"_error"]

        writer = csv.DictWriter(resultfile, fieldnames=cols)
        headers = dict( (n,n) for n in cols )
        writer.writerow(headers)

        for config,v in aggregated.iteritems():
            for sendInt in sorted(v.keys()):
                result = { 'config': config,
                                  'sendInt': sendInt,
                                  }
                for k in measures: 
                    #print v[sendInt]
                    (m,h) = mean_confidence_interval(v[sendInt][k].values())

                    if np.isnan(m):# TODO remove
                        m = 0
                    if np.isnan(h):# TODO remove
                        h = 0
                    #h = 0 # TODO remove
                    result[k] = m
                    result[k+"_error"] = h
                writer.writerow(result)

    with open(args.results+'/per_host.csv','w') as resultfile:
        sets = set()
        
        perhost = {}
        for r in runs:
            for host in allhosts:
                setname = "%s-%s-%s-"%(r.param['configname'],r.param['sendInt'],r.param['seedset'])
                sets.add(setname+"received")
                sets.add(setname+"lost")
                if r.hosts.has_key(host):
                    received = r.hosts[host]['sinkRcvdPk:count']
                    lost = r.hosts[host]['sentPk:count']-r.hosts[host]['sinkRcvdPk:count']
                else:
                    received = 0
                    lost = 100

                perhost.setdefault(host,{})[setname+"received"] = received
                perhost[host][setname+"lost"] = lost

        cols = ['address']
        cols += sorted(sets)
        print cols

        writer = csv.DictWriter(resultfile, fieldnames=cols)
        headers = dict( (n,n) for n in cols )
        writer.writerow(headers)

        for host, v in perhost.iteritems():
            data = {'address': host+1}
            data.update(v)
            writer.writerow(data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('results', help='Directory with result files')
    args = parser.parse_args()

    main(args)
        