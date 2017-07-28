#!/usr/bin/env python

import luigi
from luigi.util import requires, inherits
import os
import itertools
import pandas as pd
from rnaseq.utils import config
from rnaseq.utils.util_functions import txt_to_excel
from rnaseq.modules.base_module import prepare
from rnaseq.modules.base_module import simple_task
from rnaseq.modules.base_module import collection_task


script_dir, script_name = os.path.split(os.path.abspath(__file__))
MODULE, _ = os.path.splitext(script_name)
KALLISTO_TO_TABLE = os.path.join(script_dir, 'kallisto_to_table.R')
DIFF_ANALYSIS = os.path.join(script_dir, 'diff_analysis.R')
QUANT_REPORT = os.path.join(script_dir, 'quant_report.R')


class quant_prepare_dir(prepare):
    _module = MODULE
    clean_dir = luigi.Parameter()
    tr_index = luigi.Parameter()
    qvalue = luigi.Parameter(default='0.05')
    logfc = luigi.Parameter(default='1')


@requires(quant_prepare_dir)
class run_kallisto(simple_task):
    '''
    quantification using kallisto
    '''

    _module = MODULE
    sample = luigi.Parameter()
    _kallisto = config.module_software['kallisto']
    kallisto_dir = config.module_dir[MODULE]['kallisto']
    fq_suffix = config.file_suffix['fq']

    def get_tag(self):
        return self.sample


@inherits(quant_prepare_dir)
class kallisto_to_matrix(simple_task):
    '''
    generate gene expression matrix from kallisto quantification results
    '''

    sample_inf = luigi.Parameter()
    gene2tr = luigi.Parameter()
    _module = MODULE
    _kallisto_to_table_r = KALLISTO_TO_TABLE
    kallisto_dir = config.module_dir[MODULE]['kallisto']
    exp_dir = config.module_dir[MODULE]['exp']

    def requires(self):
        sample_list = [each.strip().split()[1]
                       for each in open(self.sample_inf)]
        return [run_kallisto(sample=each_sample,
                             clean_dir=self.clean_dir,
                             tr_index=self.tr_index,
                             proj_dir=self.proj_dir)
                for each_sample in sample_list]


@requires(kallisto_to_matrix)
class run_diff(simple_task):
    '''
    run diff analysis for each compare
    '''
    compare = luigi.Parameter()
    _module = MODULE
    _diff_analysis_r = DIFF_ANALYSIS
    kallisto_dir = config.module_dir[MODULE]['kallisto']
    exp_dir = config.module_dir[MODULE]['exp']
    diff_dir = config.module_dir[MODULE]['diff']

    def get_tag(self):
        return self.compare


@inherits(kallisto_to_matrix)
class get_excel_table(simple_task):

    _module = MODULE
    contrasts = luigi.Parameter(default='')

    def requires(self):
        if not self.contrasts:
            group_sample_df = pd.read_table(
                self.sample_inf, header=None, index_col=0)
            compare_list = itertools.combinations(
                group_sample_df.index.unique(), 2)
            compare_name_list = ['{0}_vs_{1}'.format(
                each_compare[0], each_compare[1])
                for each_compare in compare_list]
        else:
            contrasts_df = pd.read_table(
                self.contrasts, header=None)
            compare_name_list = ['{0}_vs_{1}'.format(contrasts_df.loc[i, 0],
                                                     contrasts_df.loc[i, 1])
                                 for i in contrasts_df.index]

        return [run_diff(compare=each_compare, proj_dir=self.proj_dir,
                         clean_dir=self.clean_dir, tr_index=self.tr_index,
                         qvalue=self.qvalue, logfc=self.logfc,
                         sample_inf=self.sample_inf, gene2tr=self.gene2tr)
                for each_compare in compare_name_list]

    def run(self):
        main_dir = os.path.join(
            self.proj_dir, config.module_dir[MODULE]['main']
        )
        for dirpath, dirnames, filenames in os.walk(main_dir):
            for each_file in filenames:
                if each_file.endswith('.txt'):
                    each_file_path = os.path.join(dirpath, each_file)
                    txt_to_excel(each_file_path)
        with self.output().open('w') as get_excel_table_log:
            get_excel_table_log.write('txt to excel finished')


@requires(get_excel_table)
class quant_report_data(simple_task):
    '''
    generate table and plots for report
    '''

    _module = MODULE
    _quant_report_r = QUANT_REPORT
    exp_dir = config.module_dir[MODULE]['exp']
    diff_dir = config.module_dir[MODULE]['diff']


@requires(quant_report_data)
class quant_collection(collection_task):
    _module = MODULE


if __name__ == '__main__':
    luigi.run()
