#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 15:51:12 2016



Please feel free to contact me for any question.
--
Zewei Song
University of Minnesota
Dept. Plant Pathology
songzewei@outlook.com
www.songzewei.org
"""

def main():
    import argparse
    import textwrap
    from lib import ParseOtuTable

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent('''\
                                    ------------------------
                                    By Zewei Song
                                    University of Minnesota
                                    Dept. Plant Pathology
                                    songzewei@outlook.com
                                    ------------------------'''), prog='fast.py -summary_otu_table')
    parser.add_argument('-otu', help='Name of the input OTU table.')
    parser.add_argument('-o', '--output', default='otu_report.txt', help='Name of the output report.')
    args = parser.parse_args()
    
    input_file = args.otu
    output_file = args.output
    
    otu_table = ParseOtuTable.parser_otu_table(input_file)

    sample_id = otu_table.sample_id
    sample_dict = otu_table.sample_dict()    
    report_dict = {}    
    for sample in sample_id:
        report_dict[sample] = sum(sample_dict[sample].values())
    
    with open(output_file, 'w') as f:
        f.write('Sample\tDepth\n')
        for sample in sample_id:
            line = ''
            line = sample + '\t' + str(report_dict[sample])
            f.write('%s\n' % line)

if __name__ == '__main__':
    main()