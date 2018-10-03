#!/usr/bin/env python

import sys
import luigi
from luigi.util import requires, inherits
import os
from rnaseq.utils import config
from rnaseq.utils.util_functions import txt_to_excel
from rnaseq.utils.util_functions import get_compare_names
from rnaseq.modules.base_module import prepare, simple_task
from rnaseq.modules.base_module import collection_task, cp_analysis_result


script_dir, script_name = os.path.split(os.path.abspath(__file__))
MODULE, _ = os.path.splitext(script_name)
KALLISTO_TO_TABLE = os.path.join(script_dir, 'kallisto_to_table.R')
DIFF_ANALYSIS = os.path.join(script_dir, 'diff_analysis.R')
QUANT_REPORT = os.path.join(script_dir, 'quant_report.R')
VENN_PLOT = os.path.join(script_dir, 'venn_plot.py')
DIFF_SEQ = os.path.join(script_dir, 'extract_diff_gene_seq.py')


class Pubvar:
    _module = MODULE


class quant_prepare_dir(prepare, Pubvar):
    clean_dir = luigi.Parameter()
    tr_index = luigi.Parameter()
    qvalue = luigi.Parameter(default='0.05')
    logfc = luigi.Parameter(default='1')


@requires(quant_prepare_dir)
class run_kallisto(simple_task, Pubvar):
    '''
    quantification using kallisto
    '''

    sample = luigi.Parameter()
    _kallisto = config.module_software['kallisto']
    kallisto_dir = config.module_dir[MODULE]['kallisto']
    fq_suffix = config.file_suffix['fq']

    def get_tag(self):
        return self.sample


@inherits(quant_prepare_dir)
class kallisto_to_matrix(simple_task, Pubvar):
    '''
    generate gene expression matrix from kallisto quantification results
    '''

    sample_inf = luigi.Parameter()
    gene2tr = luigi.Parameter()
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
class run_diff(simple_task, Pubvar):
    '''
    run diff analysis for each compare
    '''
    compare = luigi.Parameter()
    _diff_analysis_r = DIFF_ANALYSIS
    kallisto_dir = config.module_dir[MODULE]['kallisto']
    exp_dir = config.module_dir[MODULE]['exp']
    diff_dir = config.module_dir[MODULE]['diff']
    _extract_diff_gene_seq_py = DIFF_SEQ

    def get_tag(self):
        return self.compare

    def treat_parameter(self):
        self.tr_fa = self.tr_index.split('.kallisto_idx')[0]


@inherits(kallisto_to_matrix)
class get_excel_table(simple_task, Pubvar):

    contrasts = luigi.Parameter(default='None')

    def requires(self):
        compare_name_list = get_compare_names(self.contrasts, self.sample_inf)

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
                    try:
                        txt_to_excel(each_file_path)
                    except:
                        print(each_file_path)
                        sys.exit(1)
        with self.output().open('w') as get_excel_table_log:
            get_excel_table_log.write('txt to excel finished')


@requires(get_excel_table)
class venn_plot(simple_task, Pubvar):

    contrasts = luigi.Parameter(default='')
    _plot_venn_py = VENN_PLOT
    exp_dir = config.module_dir[MODULE]['exp']
    diff_dir = config.module_dir[MODULE]['diff']

    def treat_parameter(self):
        self.compare_name_list = get_compare_names(
            self.contrasts, self.sample_inf)
        self.compare_name_str = ','.join(self.compare_name_list)


@requires(venn_plot)
class quant_report_data(simple_task, Pubvar):
    '''
    generate table and plots for report
    '''

    _quant_report_r = QUANT_REPORT
    exp_dir = config.module_dir[MODULE]['exp']
    diff_dir = config.module_dir[MODULE]['diff']


@requires(quant_report_data)
class quant_collection(collection_task, Pubvar):
    pass


@requires(quant_collection)
class quant_results(cp_analysis_result, Pubvar):
    proj_name = luigi.Parameter()
    main_dir = config.module_dir[Pubvar._module]['main']
    result_dir = config.module_dir['result']['result']
    report_data = config.module_dir['result']['report_data']


if __name__ == '__main__':
    luigi.run()
