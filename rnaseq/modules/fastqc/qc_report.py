#!/usr/bin/env python

import luigi
from luigi.util import requires, inherits
import os
import pandas as pd
from rnaseq.utils import config
from rnaseq.modules.base_module import prepare
from rnaseq.modules.base_module import simple_task, simple_task_test
from rnaseq.modules.base_module import collection_task

script_dir, script_name = os.path.split(os.path.abspath(__file__))
MODULE, _ = os.path.splitext(script_name)
GC_PLOT_R = os.path.join(script_dir, 'gc_plot_report.R')
RQ_PLOT_R = os.path.join(script_dir, 'reads_quality_plot_report.R')
FASTQC_SUMMERY = os.path.join(script_dir, 'fastqc_summary_report.py')
FQ_CFG = os.path.join(script_dir, 'get_fq_cfg.py')


class fastqc_prepare(prepare):
    _module = MODULE


# @requires(fastqc_prepare)
# class get_fq_cfg(simple_task):
#     '''
#     get fastq config file
#     '''
#     _script = FQ_CFG
#     cfg = config.file_suffix[MODULE]['fq_cfg']


@requires(fastqc_prepare)
class run_fastqc(simple_task):
    '''
    run fastqc
    '''

    sample = luigi.Parameter()
    read1 = luigi.Parameter()
    read2 = luigi.Parameter()
    _module = MODULE
    fastqc_dir = config.module_dir[MODULE]['fastqc']
    fastqc_bin = config.module_software[MODULE]

    def get_tag(self):
        return self.sample


@inherits(fastqc_prepare)
class fastqc_summary(simple_task):
    '''
    generate fastqc summary table
    '''

    sample_inf = luigi.Parameter()
    _module = MODULE
    _script = FASTQC_SUMMERY
    _dir = config.module_dir[MODULE]['main']

    def requires(self):
        sample_df = pd.read_table(self.sample_inf, header=None,
                                  names=['read1', 'read2'], index_col=0)
        return [run_fastqc(sample=sample,
                           read1=sample_df.loc[sample, 'read1'],
                           read2=sample_df.loc[sample, 'read2'],
                           proj_dir=self.proj_dir)
                for sample in sample_df.index]


@requires(fastqc_summary)
class gc_plot(simple_task):
    '''
    plot gc graph
    '''
    _module = MODULE
    _script = GC_PLOT_R
    _dir = config.module_dir[MODULE]['gc']


@requires(gc_plot)
class reads_quality_plot(simple_task):
    '''
    plot reads quality
    '''
    _module = MODULE
    _script = RQ_PLOT_R
    _dir = config.module_dir[MODULE]['reads_quality']


@requires(reads_quality_plot)
class fastqc_report(simple_task):
    '''
    print fastqc report
    '''
    _module = MODULE
    proj_name = luigi.Parameter()
    _dir = config.module_dir[MODULE]['main']


@requires(fastqc_report)
class fastqc_collection(collection_task):
    _module = MODULE


if __name__ == '__main__':
    luigi.run()
