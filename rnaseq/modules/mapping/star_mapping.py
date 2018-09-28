#!/usr/bin/env python

import luigi
from luigi.util import requires, inherits
import os
from rnaseq.utils import config
from rnaseq.modules.base_module import prepare, simple_task
from rnaseq.modules.base_module import collection_task, cp_analysis_result


script_dir, script_name = os.path.split(os.path.abspath(__file__))
MODULE, _ = os.path.splitext(script_name)
STAR_THREAD = 8
STAR_MAPPING_STATS = os.path.join(script_dir, 'star_mapping_stats.py')
STAR_MAPPING_STATS_PLOT = os.path.join(script_dir, 'star_mapping_stats_plot.R')


class Pubvar:
    _module = MODULE


class mapping_prepare_dir(prepare, Pubvar):
    clean_dir = luigi.Parameter()
    star_index = luigi.Parameter()


@requires(mapping_prepare_dir)
class run_star(simple_task, Pubvar):
    '''
    run star mapping using ENCODE options
    '''
    sample = luigi.Parameter()
    fq_suffix = config.file_suffix['fq']
    _mapping_dir = config.module_dir[MODULE]['map']
    _star = config.module_software[MODULE]
    _thread = STAR_THREAD

    def get_tag(self):
        return self.sample


@requires(run_star)
class get_bam_file(simple_task, Pubvar):
    '''
    1. link star output bam to bam dir
    2. make bam index
    '''
    _bam_dir = config.module_dir[MODULE]['bam']
    _mapping_dir = config.module_dir[MODULE]['map']

    def get_tag(self):
        return self.sample


@inherits(mapping_prepare_dir)
class star_mapping_summary(simple_task, Pubvar):
    '''
    combine mapping stats of all samples and plot
    '''

    sample_inf = luigi.Parameter()
    _stats_script = STAR_MAPPING_STATS
    _plot_script = STAR_MAPPING_STATS_PLOT
    _mapping_dir = config.module_dir[MODULE]['map']
    _main_dir = config.module_dir[MODULE]['main']

    def requires(self):
        sample_list = [each.strip().split()[1]
                       for each in open(self.sample_inf)]
        return [get_bam_file(sample=each_sample,
                             proj_dir=self.proj_dir,
                             clean_dir=self.clean_dir,
                             star_index=self.star_index)
                for each_sample in sample_list]


@requires(star_mapping_summary)
class star_mapping_collection(collection_task, Pubvar):
    pass


@requires(star_mapping_collection)
class star_mapping_results(cp_analysis_result, Pubvar):
    proj_name = luigi.Parameter()
    main_dir = config.module_dir[Pubvar._module]['main']
    result_dir = config.module_dir['result']['result']
    report_data = config.module_dir['result']['report_data']


if __name__ == '__main__':
    luigi.run()
