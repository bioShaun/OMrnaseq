import pandas as pd
from pandas import DataFrame
import numpy as np
import click
from rnaseq.utils import config
from rnaseq.utils.util_functions import save_mkdir
import os
import random
import envoy
import string
import itertools


script_dir, script_name = os.path.split(os.path.abspath(__file__))
GC_PLOT_R = os.path.join(script_dir, 'gc_plot_report.R')
RQ_PLOT_R = os.path.join(script_dir, 'reads_quality_plot_report.R')
MODULE = 'fastqc'


QC_DATA_SUMMARY_HEADER = [
    'sample_id',
    'reads_num',
    'reads_len',
    'data_size',
    'q30',
    'gc'
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
    return ['{abbr}_{n:0>4d}'.format(abbr=abbr, n=n+1)
            for n in range(num)]


def generate_sample_data(min_val, max_val, num, step=0.01):
    data_pool = np.arange(min_val, max_val, step)
    return np.random.choice(data_pool, num)


def data_size_upper(data_size, rel_size=0.2, abs_size=5):
    return data_size + max(data_size * rel_size, abs_size)


@click.command()
@click.option(
    '-p',
    '--proj_dir',
    help='project directory.',
    type=click.Path(),
    required=True
)
@click.option(
    '-s',
    '--sample_num',
    help='sample number.',
    type=click.INT,
    required=True
)
@click.option(
    '-d',
    '--data_size',
    help='data size.',
    type=click.FLOAT,
    default=10.0
)
@click.option(
    '-a',
    '--name_abbr',
    help='sample name abbr.',
    type=click.STRING,
    default=''
)
def main(proj_dir, name_abbr, sample_num, data_size):
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
    data_summary_dict['sample_id'] = generate_sample_name(name_abbr, sample_num)
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
    data_summary_df.loc[:, 'reads_num'] = data_summary_df.data_size * 1000 / 150
    data_summary_df.loc[:, 'reads_len'] = 'PE150'
    data_summary_df.to_csv(qc_summary_file, sep='\t',
                           index=False, float_format='%.2f',
                           columns=QC_DATA_SUMMARY_HEADER)


if __name__ == '__main__':
    main()