#!/usr/bin/env python

import luigi
from luigi.util import requires, inherits
import os
import envoy
from rnaseq.utils import config
from rnaseq.utils.util_functions import rsync_pattern_to_file
from rnaseq.utils.util_functions import write_obj_to_file

script_dir = os.path.dirname(os.path.abspath(__file__))
GC_PLOT_R = os.path.join(script_dir, 'gc_plot.R')
RQ_PLOT_R = os.path.join(script_dir, 'reads_quality_plot.R')
FASTQC_SUMMERY = os.path.join(script_dir, 'fastqc_summary.py')


class prepare_dir(luigi.Task):

    proj_dir = luigi.Parameter()
    clean_dir = luigi.Parameter()

    def run(self):
        with self.output().open('w') as prepare_dir_log:
            for each_module in config.module_dir['fastqc']:
                each_module_dir = os.path.join(
                    self.proj_dir, config.module_dir['fastqc'][each_module])
                config.module_dir['fastqc'][each_module] = each_module_dir
                try:
                    os.makedirs(each_module_dir)
                except OSError:
                    prepare_dir_log.write(
                        '{each_module_dir} has been built before.'.format(**locals()))

    def output(self):
        return luigi.LocalTarget('{t.proj_dir}/{log_dir}/prepare_dir.log'.format(
            t=self, log_dir=config.module_dir['fastqc']['logs']))


@requires(prepare_dir)
class run_fastqc(luigi.Task):
    '''
    run fastqc
    '''

    sample = luigi.Parameter()

    def run(self):
        fastqc_dir = config.module_dir['fastqc']['fastqc']
        fastqc_bin = config.module_software['fastqc']
        fq1, fq2 = ['{t.clean_dir}/{t.sample}_{each}.{fq_suffix}'.format(
            t=self, each=each_read, fq_suffix=config.file_suffix['fq']
        ) for each_read in (1, 2)]
        fastqc_cmd = '{fastqc_bin} {fq1} {fq2} --extract -o {fastqc_dir}'.format(
            **locals()
        )
        fastqc_process = envoy.run(fastqc_cmd)
        with self.output().open('w') as fastqc_log:
            fastqc_log.write(fastqc_process.std_err)

    def output(self):
        return luigi.LocalTarget('{log_dir}/{t.sample}.fastqc.log'.format(
            log_dir=config.module_dir['fastqc']['logs'], t=self))


@inherits(prepare_dir)
class fastqc_summary(luigi.Task):
    '''
    generate fastqc summary table
    '''

    sample_inf = luigi.Parameter()

    def requires(self):
        sample_list = [each.strip().split()[1]
                       for each in open(self.sample_inf)]
        return [run_fastqc(sample=each_sample, clean_dir=self.clean_dir, proj_dir=self.proj_dir) for each_sample in sample_list]

    def run(self):
        fastqc_summary_cmd = 'python {script} {t.sample_inf} {_dir} {_dir}/fastqc_general_stats'.format(
            script=FASTQC_SUMMERY, t=self, _dir=config.module_dir['fastqc']['main']
        )
        fastqc_summary_process = envoy.run(fastqc_summary_cmd)
        with self.output().open('w') as fastqc_summary_log:
            fastqc_summary_log.write(fastqc_summary_process.std_err)

    def output(self):
        return luigi.LocalTarget('{log_dir}/fastqc_summary.log'.format(
            log_dir=config.module_dir['fastqc']['logs']
        ))


@requires(fastqc_summary)
class gc_plot(luigi.Task):
    '''
    plot gc graph
    '''

    def run(self):
        gc_dir = config.module_dir['fastqc']['gc']
        gc_cmd = '{_R} {script} --gc_dir {_dir} --sample_inf {t.sample_inf}'.format(
            _R=config.module_software['Rscript'], script=GC_PLOT_R,
            _dir=gc_dir, t=self
        )
        gc_process = envoy.run(gc_cmd)
        with self.output().open('w') as gc_plot_log:
            gc_plot_log.write(gc_process.std_err)

    def output(self):
        return luigi.LocalTarget('{log_dir}/gc_plot.log'.format(
            log_dir=config.module_dir['fastqc']['logs']
        ))


@requires(gc_plot)
class reads_quality_plot(luigi.Task):
    '''
    plot reads quality
    '''

    def run(self):
        reads_quality_dir = config.module_dir['fastqc']['reads_quality']
        reads_quality_cmd = '{_R} {script} {_dir} {t.sample_inf}'.format(
            _R=config.module_software['Rscript'], script=RQ_PLOT_R,
            _dir=reads_quality_dir, t=self
        )
        reads_quality_process = envoy.run(reads_quality_cmd)
        with self.output().open('w') as reads_quality_plot_log:
            reads_quality_plot_log.write(reads_quality_process.std_err)

    def output(self):
        return luigi.LocalTarget('{log_dir}/reads_quality_plot.log'.format(
            log_dir=config.module_dir['fastqc']['logs']
        ))


@requires(reads_quality_plot)
class fastqc_collection(luigi.Task):
    '''
    generate config file for analysis results and analysis report
    .ignore: files not needed in analysis results
    .report_files: files needed for generate report
    '''

    def run(self):
        ignore_files = ['.ignore', 'logs',
                        'fastqc_results/*zip', '.report_files']
        pdf_report_files_pattern = ['fastqc_general_stats.txt',
                                    'gc_plot/*gc_distribution.line.png',
                                    'reads_quality_plot/*reads_quality.bar.png']
        pdf_report_files = rsync_pattern_to_file(
            config.module_dir['fastqc']['main'], pdf_report_files_pattern)
        pdf_report_ini = os.path.join(config.module_dir['fastqc']['main'], '.report_files')
        write_obj_to_file(pdf_report_files, pdf_report_ini)
        with self.output().open('w') as ignore_files_inf:
            for each_file in ignore_files:
                ignore_files_inf.write('{}\n'.format(each_file))

    def output(self):
        return luigi.LocalTarget('{main_dir}/.ignore'.format(
            main_dir=config.module_dir['fastqc']['main']
        ))


if __name__ == '__main__':
    luigi.run()
