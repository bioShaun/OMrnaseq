#! /usr/bin/python

import luigi
from luigi.util import requires, inherits
import os
<<<<<<< HEAD
import envoy
from rnaseq.utils import config
from rnaseq.utils.util_functions import write_obj_to_file
from rnaseq.utils.util_functions import prepare_dir


script_dir = os.path.dirname(os.path.abspath(__file__))
=======
from rnaseq.utils import config
from rnaseq.modules.base_module import prepare
from rnaseq.modules.base_module import simple_task_test
from rnaseq.modules.base_module import collection_task


script_dir, script_name = os.path.split(os.path.abspath(__file__))
MODULE, _ = os.path.splitext(script_name)
>>>>>>> 4e136c66d0d8b2f7604b5a1b2d3b063655e6f6a7
STAR_THREAD = 8
STAR_MAPPING_STATS = os.path.join(script_dir, 'star_mapping_stats.py')
STAR_MAPPING_STATS_PLOT = os.path.join(script_dir, 'star_mapping_stats_plot.R')


<<<<<<< HEAD
class prepare_dir(prepare_dir):

    _module = 'mapping'



# class run_star(luigi.Task):
#     '''
#     run mapping
#     '''
#     sample = luigi.Parameter()
#     OutDir = luigi.Parameter()
#
#     def requires(self):
#         return prepare(OutDir=OutDir)
#
#     def run(self):
#         each_sample_mapping_dir = path.join(OutDir, 'mapping_dir', self.sample)
#         if not path.exists(each_sample_mapping_dir):
#             system('mkdir -p {}'.format(each_sample_mapping_dir))
#
#         tmp = run_cmd(['STAR',
#                        '--genomeDir',
#                        IndexDir,
#                        '--readFilesIn',
#                        '{0}/{1}_1.clean.fq.gz'.format(CleanDir, self.sample),
#                        '{0}/{1}_2.clean.fq.gz'.format(CleanDir, self.sample),
#                        '--readFilesCommand zcat',
#                        '--outFileNamePrefix',
#                        '{0}/mapping_dir/{1}/'.format(OutDir, self.sample),
#                        '--runThreadN',
#                        '{}'.format(STAR_THREAD),
#                        '--outSAMtype BAM SortedByCoordinate',
#                        '--outSAMstrandField intronMotif',
#                        '--outFilterType BySJout',
#                        '--outFilterMultimapNmax 20',
#                        '--alignSJoverhangMin 8',
#                        '--alignSJDBoverhangMin 1',
#                        '--outFilterMismatchNmax 999',
#                        '--alignIntronMin 20',
#                        '--alignIntronMax 1000000',
#                        '--alignMatesGapMax 1000000'])
#
#         with self.output().open('w') as mapping_log:
#             mapping_log.write(tmp)
#
#     def output(self):
#         return luigi.LocalTarget('{0}/logs/{1}.mapping.log'.format(OutDir, self.sample))
#
#
# class get_bam_file(luigi.Task):
#     '''
#     link star output bam to bam dir
#     '''
#
#     sample = luigi.Parameter()
#     OutDir = luigi.Parameter()
#
#     def requires(self):
#         return [run_star(sample=each_sample, OutDir=OutDir) for each_sample in sample_list]
#
#     def run(self):
#         link_cmd = ['ln',
#                     '-s',
#                     '{0}/mapping_dir/{1}/Aligned.sortedByCoord.out.bam'.format(
#                         OutDir, self.sample),
#                     '{0}/bam_dir/{1}.bam'.format(OutDir, self.sample)]
#
#         index_cmd = ['samtools',
#                      'index',
#                      '{0}/bam_dir/{1}.bam'.format(OutDir, self.sample)]
#         cmd_list = [link_cmd, index_cmd]
#
#         tmp = run_cmd(cmd_list)
#
#         with self.output().open('w') as get_bam_file_log:
#             get_bam_file_log.write(tmp)
#
#     def output(self):
#         return luigi.LocalTarget('{0}/logs/{1}.get_bam_file.log'.format(OutDir, self.sample))
#
#
# class star_mapping_summary(luigi.Task):
#
#     OutDir = luigi.Parameter()
#
#     def requires(self):
#         return [get_bam_file(sample=each_sample, OutDir=OutDir) for each_sample in sample_list]
#
#     def run(self):
#
#         summary_stats_cmd = ['python',
#                              STAR_MAPPING_STATS,
#                              SampleInf,
#                              '{}/mapping_dir/'.format(OutDir),
#                              '{}/mapping_stats'.format(OutDir)]
#
#         summary_plot_cmd = ['Rscript',
#                             STAR_MAPPING_STATS_PLOT,
#                             '--sample_inf',
#                             SampleInf,
#                             '--mapping_stats',
#                             '{}/mapping_stats.plot'.format(OutDir),
#                             '--out_dir',
#                             OutDir]
#
#         star_mapping_summary_log_inf = run_cmd(
#             [summary_stats_cmd, summary_plot_cmd])
#
#         with self.output().open('w') as star_mapping_summary_log:
#             star_mapping_summary_log.write(star_mapping_summary_log_inf)
#
#     def output(self):
#         return luigi.LocalTarget('{}/logs/star_mapping_summary.log'.format(OutDir))
#
#
# class star_mapping_collection(luigi.Task):
#
#     OutDir = luigi.Parameter()
#     SampleInf = luigi.Parameter()
#     CleanDir = luigi.Parameter()
#     IndexDir = luigi.Parameter()
#
#     def requires(self):
#         global OutDir, SampleInf, CleanDir, IndexDir, sample_list
#         OutDir = self.OutDir
#         SampleInf = self.SampleInf
#         CleanDir = self.CleanDir
#         IndexDir = self.IndexDir
#         sample_list = [each.strip().split()[1] for each in open(SampleInf)]
#         return star_mapping_summary(OutDir=OutDir)
#
#     def run(self):
#         ignore_files = ['.ignore', 'logs', 'mapping_dir',
#                         'bam_dir', 'mapping_stats.plot', 'Rplots.pdf', 'mapping_stats.report']
#         pdf_report_files = ['mapping_stats_plot.png', 'mapping_stats.report', 'mapping_stats.txt']
#         pdf_report_ini = path.join(self.OutDir, '.report_files')
#         write_obj_to_file(pdf_report_files, pdf_report_ini)
#         with self.output().open('w') as ignore_files_inf:
#             for each_file in ignore_files:
#                 ignore_files_inf.write('{}\n'.format(each_file))
#
#     def output(self):
#         return luigi.LocalTarget('{}/.ignore'.format(self.OutDir))
=======
class mapping_prepare_dir(prepare):
    _module = MODULE
    clean_dir = luigi.Parameter()
    star_index = luigi.Parameter()


@requires(mapping_prepare_dir)
class run_star(simple_task_test):
    '''
    run star mapping using ENCODE options
    '''
    sample = luigi.Parameter()
    fq_suffix = config.file_suffix['fq']
    _mapping_dir = config.module_dir[MODULE]['map']
    _star = config.module_software[MODULE]
    _module = MODULE
    _thread = STAR_THREAD

    def get_tag(self):
        return self.sample


@requires(run_star)
class get_bam_file(simple_task_test):
    '''
    1. link star output bam to bam dir
    2. make bam index
    '''
    _bam_dir = config.module_dir[MODULE]['bam']
    _mapping_dir = config.module_dir[MODULE]['map']
    _module = MODULE

    def get_tag(self):
        return self.sample


@inherits(mapping_prepare_dir)
class star_mapping_summary(simple_task_test):
    '''
    combine mapping stats of all samples and plot
    '''

    sample_inf = luigi.Parameter()
    _stats_script = STAR_MAPPING_STATS
    _plot_script = STAR_MAPPING_STATS_PLOT
    _mapping_dir = config.module_dir[MODULE]['map']
    _main_dir = config.module_dir[MODULE]['main']
    _R = config.module_software['Rscript']
    _module = MODULE

    def requires(self):
        sample_list = [each.strip().split()[1]
                       for each in open(self.sample_inf)]
        return [get_bam_file(sample=each_sample, proj_dir=self.proj_dir, clean_dir=self.clean_dir, star_index=self.star_index)
                for each_sample in sample_list]


@requires(star_mapping_summary)
class star_mapping_collection(collection_task):
    _module = MODULE
    pass
>>>>>>> 4e136c66d0d8b2f7604b5a1b2d3b063655e6f6a7


if __name__ == '__main__':
    luigi.run()
