#!/usr/bin/env python

import luigi
from luigi.util import requires, inherits
import os
from rnaseq.utils import config
from rnaseq.modules.base_module import prepare
from rnaseq.modules.base_module import simple_task
from rnaseq.modules.base_module import collection_task


script_dir, script_name = os.path.split(os.path.abspath(__file__))
MODULE, _ = os.path.splitext(script_name)
KALLISTO_TO_TABLE = os.path.join(script_dir, 'kallisto_to_table.R')
DIFF_ANALYSIS


class quant_prepare_dir(prepare):
    _module = MODULE
    clean_dir = luigi.Parameter()
    tr_index = luigi.Parameter()


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
    _R = config.module_software['Rscript']
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



# class run_diff(luigi.Task):
#     '''
#     run diff analysis for each compare
#     '''
#
#     compare = luigi.Parameter()
#     OutDir = luigi.Parameter()
#
#     def requires(self):
#         return kallisto_to_matrix(OutDir=OutDir)
#
#     def run(self):
#         diff_cmd = ['Rscript',
#                     DIFF_ANALYSIS,
#                     '--kallisto_dir',
#                     '{}/kallisto'.format(OutDir),
#                     '--tpm_table',
#                     '{}/expression_summary/Gene.tpm.txt'.format(OutDir),
#                     '--compare',
#                     self.compare,
#                     '--sample_inf',
#                     SampleInf,
#                     '--gene2tr',
#                     Gene2Tr,
#                     '--out_dir',
#                     '{0}/differential_analysis/{1}'.format(OutDir, self.compare)]
#
#         diff_inf = run_cmd(diff_cmd)
#         with self.output().open('w') as diff_log:
#             diff_log.write(diff_inf)
#
#     def output(self):
#         return luigi.LocalTarget('{0}/logs/diff_analysis_{1}.log'.format(OutDir, self.compare))
#
#
# class get_excel_table(luigi.Task):
#
#     '''
#     generate excel format table
#     '''
#     OutDir = luigi.Parameter()
#
#     def requires(self):
#         return [run_diff(compare=each_compare, OutDir=OutDir) for each_compare in compare_name_list]
#
#     def run(self):
#
#         for dirpath, dirnames, filenames in walk(OutDir):
#             for each_file in filenames:
#                 if each_file.endswith('.txt'):
#                     each_file_path = path.join(dirpath, each_file)
#                     txt_to_excel(each_file_path)
#
#         with self.output().open('w') as get_excel_table_log:
#             get_excel_table_log.write('txt to excel finished')
#
#     def output(self):
#         return luigi.LocalTarget('{0}/logs/get_excel_table.log'.format(OutDir))
#
#
# class report_data(luigi.Task):
#     '''
#     generate table and plots for report
#     '''
#     OutDir = luigi.Parameter()
#
#     def requires(self):
#         return get_excel_table(OutDir=OutDir)
#
#     def run(self):
#         report_tb_cmd = ['Rscript',
#                          QUANT_REPORT,
#                          '--quant_dir',
#                          OutDir,
#                          '--sample_inf',
#                          SampleInf]
#
#         report_tb_inf = run_cmd(report_tb_cmd)
#         with self.output().open('w') as report_log:
#             report_log.write(report_tb_inf)
#
#     def output(self):
#         return luigi.LocalTarget('{0}/logs/report_data.log'.format(OutDir))
#
#
# class quant_collection(luigi.Task):
#
#     OutDir = luigi.Parameter()
#     SampleInf = luigi.Parameter()
#     CleanDir = luigi.Parameter()
#     Transcript = luigi.Parameter()
#     Gene2Tr = luigi.Parameter()
#
#     def requires(self):
#         global OutDir, SampleInf, CleanDir, sample_list
#         global Transcript, Gene2Tr, compare_name_list
#         OutDir = self.OutDir
#         SampleInf = self.SampleInf
#         CleanDir = self.CleanDir
#         Transcript = self.Transcript
#         Gene2Tr = self.Gene2Tr
#         group_sample_df = pd.read_table(
#             self.SampleInf, header=None, index_col=0)
#         compare_list = itertools.combinations(
#             group_sample_df.index.unique(), 2)
#         compare_name_list = ['{0}_vs_{1}'.format(
#             each_compare[0], each_compare[1]) for each_compare in compare_list]
#         sample_list = [each.strip().split()[1] for each in open(SampleInf)]
#         return report_data(OutDir=OutDir)
#
#     def run(self):
#         ignore_files = ['.ignore', 'logs', 'kallisto/*/run_info.json',
#                         '.report_files', 'Rplots.pdf',
#                         'expression_summary/pdf.*',
#                         'expression_summary/html.*']
#         report_files_pattern = ['expression_summary/*.png',
#                         'differential_analysis/*/*png',
#                         'expression_summary/*Gene.tpm.txt',
#                         'expression_summary/*example.diff.table.txt',
#                         'differential_analysis/*/*.edgeR.DE_results.txt']
#         report_files = rsync_pattern_to_file(self.OutDir, report_files_pattern)
#         report_ini = path.join(self.OutDir, '.report_files')
#         write_obj_to_file(report_files, report_ini)
#         with self.output().open('w') as ignore_inf:
#             for each_file in ignore_files:
#                 ignore_inf.write('{}\n'.format(each_file))
#
#     def output(self):
#         return luigi.LocalTarget('{}/.ignore'.format(self.OutDir))


if __name__ == '__main__':
    luigi.run()
