#!/usr/bin/env python

import luigi
import os
from rnaseq.utils import config
import envoy
from rnaseq.utils.util_functions import rsync_pattern_to_file
from rnaseq.utils.util_functions import write_obj_to_file
from rnaseq.utils.util_functions import purge
import sys


class prepare(luigi.Task):

    proj_dir = luigi.Parameter()
    _module = 'test'

    def run(self):
        prepare_dir_log_list = []
        for each_module in config.module_dir[self._module]:
            each_module_dir = os.path.join(
                self.proj_dir, config.module_dir[self._module][each_module])
            try:
                os.makedirs(each_module_dir)
            except OSError:
                prepare_dir_log_list.append(
                    '{_dir} has been built before.\n'.format(
                        _dir=each_module_dir
                    ))
        with self.output().open('w') as prepare_dir_log:
            for eachline in prepare_dir_log_list:
                prepare_dir_log.write(eachline)

    def output(self):
        return luigi.LocalTarget('{t.proj_dir}/{_dir}/prepare_dir.log'.format(
            t=self, _dir=config.module_dir[self._module]['logs']))


class simple_task(luigi.Task):

    _tag = 'analysis'
    _module = 'test'
    proj_dir = luigi.Parameter()
    _R = config.module_software['Rscript']

    def get_tag(self):
        return self._tag

    def treat_parameter(self):
        pass

    def run(self):
        self.treat_parameter()
        class_name = self.__class__.__name__
        _run_cmd = config.module_cmd[self._module][class_name].format(
            t=self)
        _process = envoy.run(_run_cmd)
        with self.output().open('w') as simple_task_log:
            simple_task_log.write(_process.std_err)

    def output(self):
        _tag = self.get_tag()
        class_name = self.__class__.__name__
        return luigi.LocalTarget('{t.proj_dir}/{_dir}/{name}.{tag}.log'.format(
            t=self, _dir=config.module_dir[self._module]['logs'],
            name=class_name, tag=_tag
        ))


class simple_task_test(simple_task):

    def run(self):
        class_name = self.__class__.__name__
        _run_cmd = config.module_cmd[self._module][class_name].format(
            t=self)
        # _process = envoy.run(_run_cmd)
        with self.output().open('w') as simple_task_log:
            # simple_task_log.write(_process.std_out)
            simple_task_log.write(_run_cmd)


# class ReRunTask(ForceableTask):
#
#     _module = 'test'
#     proj_dir = luigi.Parameter()
#     re_launch = luigi.Parameter(default='')
#
#     def rm_logs(self, rm_list):
#         for each_file in rm_list:
#             purge(each_file)
#
#     def run(self):
#         print 'hh' * 20
#         # if not self.re_launch:
#         #     return 0
#         # module_name_list = config.module_name[self._module]
#         # remove_log_list = ['{t.proj_dir}/.ignore'.format(t=self)]
#         #
#         # if self.re_launch == 'check':
#         #     self.rm_logs(remove_log_list)
#         #     return 1
#         # elif self.re_launch == 'all':
#         #     module_index = 0
#         # elif self.re_launch not in module_name_list:
#         #     print 'wrong re-run value.'
#         #     print 're-run values: check, all, {modules}.'.format(
#         #         modules=', '.join(module_name_list)
#         #     )
#         #     sys.exit(1)
#         # else:
#         #     module_index = module_name_list.index(self.re_launch)
#         # re_run_modules = module_name_list[module_index:]
#         # remove_log_list.extend(['{t.proj_dir}/{log}/{name}.*log'.format(
#         #     t=self, log=config.module_dir[self._module]['logs'], name=name
#         # ) for name in re_run_modules])
#         # self.rm_logs(remove_log_list)
#
#     #     with self.output().open('w') as re_run_inf:
#     #         re_run_inf.write('re-run [{t.re_launch}]'.format(t=self))
#     #
#     def output(self):
#         return luigi.LocalTarget('{t.proj_dir}/{log_dir}/re_run.log'.format(
#             t=self, log_dir=config.module_dir[self._module]['logs']
#         ))


class collection_task(luigi.Task):
    '''
    generate config file for analysis results and analysis report
    .ignore: files not needed in analysis results
    .report_files: files needed for generate report
    '''
    _module = 'test'
    proj_dir = luigi.Parameter()

    def run(self):
        pdf_report_ini = os.path.join(
            self.proj_dir, config.module_dir[self._module]['main'])
        ignore_files = config.module_file[self._module]['ignore_files']
        if 'pdf_files' in config.module_file[self._module]:
            pdf_report_files = rsync_pattern_to_file(
                pdf_report_ini, config.module_file[self._module]['pdf_files'])
            pdf_report_ini = os.path.join(
                pdf_report_ini, '.report_files')
            write_obj_to_file(pdf_report_files, pdf_report_ini)
        with self.output().open('w') as ignore_files_inf:
            for each_file in ignore_files:
                ignore_files_inf.write('{}\n'.format(each_file))

    def output(self):
        return luigi.LocalTarget('{t.proj_dir}/{main_dir}/.ignore'.format(
            t=self, main_dir=config.module_dir[self._module]['main']
        ))


class cp_analysis_result(simple_task):

    _tag = 'cp_results'
    _module = 'test'
    proj_dir = luigi.Parameter()

    def run(self):
        _run_cmd = config.module_cmd['cp_results'].format(
            t=self)
        _process = envoy.run(_run_cmd)
        with self.output().open('w') as simple_task_log:
            simple_task_log.write(_process.std_err)
