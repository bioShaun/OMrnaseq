#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import pandas as pd
from pandas import DataFrame, Series
import numpy as np
from rnaseq.utils import config
from rnaseq.utils.util_functions import save_mkdir
import os
import random
import envoy
import string
import itertools
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


script_dir, script_name = os.path.split(os.path.abspath(__file__))
GC_PLOT_R = os.path.join(script_dir, 'gc_plot.R')
RQ_PLOT_R = os.path.join(script_dir, 'reads_quality_plot.R')
GC_TEST_DATA = os.path.join(script_dir, 'test_data', 'unstrand.gc.txt')
READS_QUAL_TEST_DATA = os.path.join(
    script_dir, 'test_data', 'reads_quality.txt')
MODULE = 'fastqc'


QC_DATA_SUMMARY_HEADER = [
    'sample_id',
    'reads_num',
    'reads_len',
    'data_size',
    'q30',
    'gc'
]

QC_DATA_OUT_HEADER = [
    'Sample_ID',
    'Reads_Number(M)',
    'Reads_Length',
    'Data_Size(G)',
    'Q30(%)',
    'GC(%)'
]


Q30_LOWER = 95
Q30_UPPER = 97
GC_LOWER = 45
GC_UPPER = 50


def generate_sample_prefix(letter_num=3):
    name_pool = itertools.combinations_with_replacement(
        string.ascii_uppercase, letter_num
    )
    return ''.join(random.choice(list(name_pool)))


def generate_sample_name(abbr, num):
    return ['{abbr}_{n:0>4d}'.format(abbr=abbr, n=n + 1)
            for n in range(num)]


def generate_sample_data(min_val, max_val, num, step=0.01):
    data_pool = np.arange(min_val, max_val, step)
    return np.random.choice(data_pool, num)


def data_size_upper(data_size, rel_size=0.2, abs_size=5):
    return data_size + max(data_size * rel_size, abs_size)


def generate_fake_gc_file(outfile, offset=0.1):
    example_df = pd.read_table(GC_TEST_DATA)
    random_num = Series(
        generate_sample_data(0, offset, len(example_df), step=0.001))
    example_df.loc[:, 'A'] = example_df.A + random_num
    example_df.loc[:, 'T'] = example_df.loc[:, 'T'] + random_num
    example_df.loc[:, 'C'] = example_df.C - random_num
    example_df.loc[:, 'G'] = example_df.G - random_num
    example_df.to_csv(outfile, sep='\t', index=False)
    return example_df


def generate_fake_rq_file(outfile, offset=0.05):
    example_df = pd.read_table(READS_QUAL_TEST_DATA)
    offset_series = Series(
        generate_sample_data(1 - offset,
                             1 + offset,
                             len(example_df))
    )
    example_df.loc[:, 'Proportion'] = example_df.Proportion * \
        offset_series
    example_df.to_csv(outfile, sep='\t', index=False)
    return example_df


def main(proj_dir, sample_num, data_size,
         project_name='测试报告', project_id='测试报告',
         company='onmath', name_abbr=''):
    # prepare working dir
    qc_main_dir = os.path.join(proj_dir,
                               config.module_dir[MODULE]['main'])
    gc_dir = os.path.join(proj_dir,
                          config.module_dir[MODULE]['gc'])
    rq_dir = os.path.join(proj_dir,
                          config.module_dir[MODULE]['reads_quality'])
    map(save_mkdir, [gc_dir, rq_dir])

    # generate data information table
    qc_summary_file = os.path.join(qc_main_dir,
                                   'fastqc_general_stats.txt')
    data_summary_dict = dict()
    if not name_abbr:
        name_abbr = generate_sample_prefix()
    data_summary_dict['sample_id'] = generate_sample_name(
        name_abbr, sample_num)
    data_summary_dict['data_size'] = generate_sample_data(
        data_size, data_size_upper(data_size), sample_num
    )
    data_summary_dict['q30'] = generate_sample_data(Q30_LOWER,
                                                    Q30_UPPER,
                                                    sample_num)
    data_summary_dict['gc'] = generate_sample_data(GC_LOWER,
                                                   GC_UPPER,
                                                   sample_num,
                                                   step=1)
    data_summary_df = DataFrame(data_summary_dict)
    data_summary_df.loc[:, 'reads_num'] = data_summary_df.data_size * \
        1000 / 150
    data_summary_df.loc[:, 'reads_len'] = 'PE150'

    # generate gc plot data & plot
    gc_files = [os.path.join(gc_dir, '{each}.gc.txt'.format(each=each))
                for each in data_summary_df.sample_id]
    map(generate_fake_gc_file, gc_files)
    envoy.run('Rscript {gc_r} --gc_dir {gc_dir}'.format(
        gc_r=GC_PLOT_R, gc_dir=gc_dir
    ))

    # generate reads quality data & plot
    rq_files = [os.path.join(rq_dir, '{each}.reads_quality.txt'.format(
        each=each
    )) for each in data_summary_df.sample_id]
    map(generate_fake_rq_file, rq_files)
    envoy.run('Rscript {rq_r} --rq_dir {rq_dir}'.format(
        rq_r=RQ_PLOT_R, rq_dir=rq_dir
    ))

    data_summary_df = data_summary_df.loc[:, QC_DATA_SUMMARY_HEADER]
    data_summary_df.columns = QC_DATA_OUT_HEADER
    data_summary_df.to_csv(qc_summary_file, sep='\t',
                           index=False, float_format='%.2f')

    # generate report
    r = envoy.run('qc_report -n {pn} -i {pi} -c {cp} {pd}'.format(
        pn=project_name, pi=project_id,
        cp=company, pd=qc_main_dir))


if __name__ == '__main__':
    main()
