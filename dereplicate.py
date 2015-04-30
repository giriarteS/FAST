# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 18:18:32 2015

Dereplicate a give FASTA file. All record with identical sequence will be grouped into one OTU
in the output OTU map.

Technically, dereplication is OTU clustering with similarity = 1.0

This script is slower than USEARCH 8.0, but does not have limitation on memory usage.

Please feel free to contact me for any question.
--
Zewei Song
University of Minnesota
Dept. Plant Pathology
songzewei@outlook.com
"""

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help='Input FASTA file to be dereplicated.')
parser.add_argument('-o', '--output', help='Name for output OTU map and FASTA file.')
parser.add_argument('-t', '--thread', default = 1, help='Number of threads to be used.')

args = parser.parse_args()

input_file = args.input
output_name = args.output
output_map = output_name + '.txt'
output_fasta = output_name + '.fasta'
thread = int(args.thread)


def dereplicate_worker(input_seqs, output_derep, n, count, total):
    # Dereplicate a chunk of input sequences
    # n is the iterate number of the worker
    # count is a shared list on number of processed sequences by each worker
    # total is a shared value for total number of sequences
    total_seqs = float(total.value)
    derep = output_derep[n]
    for record in input_seqs:
        try:
            derep[record[1]].append(record[0])
        except KeyError:
            derep[record[1]] = [record[0]]
        count[n] += 1
        if n == 0:
            print str(round((sum(count) / total_seqs * 100), 2)) + '%' + '\b' * 50,
    output_derep[n] = derep


def divide_seqs(total, thread_num):
    # Set break point for input sequences
    seqs_divide = []
    start = 0
    size = total / thread_num
    for i in range(thread):
        seqs_divide.append([start, start + size])
        start += size
    seqs_divide[-1][-1] += total % thread_num
    return seqs_divide


if __name__ == '__main__':
    import time
    from lib import File_IO
    from multiprocessing import Process, Manager, Value

    print 'Using %i threads ...' % thread

    input_file = input_file
    print 'Loading %s ...' % input_file
    seqs = File_IO.read_seqs(input_file)
    seqs_num = Value('i', len(seqs))
    print 'Read in %i sequences.' % seqs_num.value

    # Separated seqs into pools
    print 'Separating raw sequences into %d jobs ...' % thread
    d = divide_seqs(seqs_num.value, thread)

    start = time.time()
    # Create shared list for store dereplicated dict and progress counter
    manager = Manager()
    derep_dict = manager.list([{}] * thread)
    count = manager.list([0] * thread)

    print 'Starting dereplicating ...'
    workers = []
    for i in range(thread):
        current_range = d[i]
        workers.append(Process(target=dereplicate_worker,
                               args=(seqs[current_range[0]:current_range[1]], derep_dict, i, count, seqs_num)))
        workers[i].start()

    for derep_worker in workers:
        derep_worker.join()
    print 'Finished dereplicating.'
    seqs = []  # Empty sequences list to free memory.

    # Merged dereplicated dictionaries into a single dict
    print
    print 'Merging %i dictionaries into one ...' % len(derep_dict)
    merged_dict = {}
    count = 0
    for d in derep_dict:
        for key, value in d.items():
            count += 1
            try:
                merged_dict[key] += value
            except KeyError:
                merged_dict[key] = value
            print 'Merging %i sequence ...' % count + '\b' * 50,
        derep_dict[0] = ''  # Empty finished dictionary to free memory.    
    print
    print "Sequences dereplicated, clapsed from %i into %i sequences." % (seqs_num.value, len(merged_dict))
    s = [len(merged_dict[i]) for i in merged_dict]
    print 'Dereplicated length: Max=%i, Min=%i, Average=%i.' % (max(s), min(s), round(float(sum(s) / len(s)), 2))
    end = time.time()
    print "Used time: " + str(end - start) + ' seconds.'
    print

    # Name the dereplicated group
    count = 0
    for key, value in merged_dict.items():  # Add group name to the end of the the name list of each group
        derep_name = 'derep_' + str(count)
        value.append(derep_name)
        count += 1

    # Output dereplicated FASTA file
    output_seq_file = output_fasta
    with open(output_seq_file, 'w') as f:
        for key, value in merged_dict.items():
            f.write('>%s\n' % value[-1])
            f.write('%s\n' % key)
    print '%s contains dereplicated sequences.' % output_fasta

    # Output Qiime style map
    with open(output_map, 'w') as f:
        for key, value in merged_dict.items():
            f.write('%s\t%s\n' % (value[-1], '\t'.join(value[:-1])))  # Use the last element as group name
    print '%s contains an OTU map for dereplicated sequences.' % output_map