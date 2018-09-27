#!/usr/bin/env python

import luigi
from luigi.util import requires, inherits
import os
from rnaseq.utils import config
from rnaseq.modules.base_module import prepare, simple_task
from rnaseq.modules.base_module import collection_task, cp_analysis_result


script_dir, script_name = os.path.split(os.path.abspath(__file__))
MODULE, _ = os.path.splitext(script_name)
GC_PLOT_R = os.path.join(script_dir, 'gc_plot.R')
RQ_PLOT_R = os.path.join(script_dir, 'reads_quality_plot.R')
FASTQC_SUMMERY = os.path.join(script_dir, 'fastqc_summary.py')


class Pubvar:
    _module = MODULE


class fastqc_prepare(prepare, Pubvar):
    clean_dir = luigi.Parameter()


@requires(fastqc_prepare)
class run_fastqc(simple_task, Pubvar):
    '''
    run fastqc
    '''

    sample = luigi.Parameter()
    fastqc_dir = config.module_dir[MODULE]['fastqc']
    fastqc_bin = config.module_software[MODULE]
    fq_suffix = config.file_suffix['fq']

    def get_tag(self):
        return self.sample


@inherits(fastqc_prepare)
class fastqc_summary(simple_task, Pubvar):
    '''
    generate fastqc summary table
    '''

    sample_inf = luigi.Parameter()
    _script = FASTQC_SUMMERY
    _dir = config.module_dir[MODULE]['main']

    def requires(self):
        sample_list = [each.strip().split()[1]
                       for each in open(self.sample_inf)]
        return [run_fastqc(sample=sample, clean_dir=self.clean_dir,
                           proj_dir=self.proj_dir) for sample in sample_list]


@requires(fastqc_summary)
class gc_plot(simple_task, Pubvar):
    '''
    plot gc graph
    '''
    _script = GC_PLOT_R
    _dir = config.module_dir[MODULE]['gc']


@requires(gc_plot)
class reads_quality_plot(simple_task, Pubvar):
    '''
    plot reads quality
    '''
    _script = RQ_PLOT_R
    _dir = config.module_dir[MODULE]['reads_quality']


@requires(reads_quality_plot)
class fastqc_collection(collection_task, Pubvar):
    pass


@requires(fastqc_collection)
class fastqc_results(cp_analysis_result, Pubvar):
    proj_name = luigi.Parameter()
    main_dir = config.module_dir[Pubvar._module]['main']
    result_dir = config.module_dir['result']['result']
    report_data = config.module_dir['result']['report_data']


if __name__ == '__main__':
    luigi.run()
