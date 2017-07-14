#!/usr/bin/env python

import luigi
import os
from rnaseq.utils import config
import envoy
from rnaseq.utils.util_functions import rsync_pattern_to_file
from rnaseq.utils.util_functions import write_obj_to_file


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
                    '{each_module_dir} has been built before.\n'.format(**locals()))
        with self.output().open('w') as prepare_dir_log:
            for eachline in prepare_dir_log_list:
                prepare_dir_log.write(eachline)

    def output(self):
        return luigi.LocalTarget('{t.proj_dir}/{log_dir}/prepare_dir.log'.format(
            t=self, log_dir=config.module_dir[self._module]['logs']))


class simple_task(luigi.Task):

    _tag = 'analysis'
    _run_cmd = None
    _module = 'test'

    def get_tag(self):
        return self._tag

    def run(self):
        _run_cmd = config.module_cmd[self._module][self.__class__.__name__].format(
            t=self)
        _process = envoy.run(_run_cmd)
        with self.output().open('w') as simple_task_log:
            simple_task_log.write(_process.std_err)

    def output(self):
        _tag = self.get_tag()
        return luigi.LocalTarget('{log_dir}/{t.__class__.__name__}.{tag}.log'.format(
            t=self, log_dir=config.module_dir[self._module]['logs'], tag=_tag
        ))


class simple_task_test(simple_task):

    def run(self):
        _run_cmd = config.module_cmd[self._module][self.__class__.__name__].format(
            t=self)
        # _process = envoy.run(_run_cmd)
        with self.output().open('w') as simple_task_log:
            # simple_task_log.write(_process.std_out)
            simple_task_log.write(_run_cmd)


class collection_task(luigi.Task):
    '''
    generate config file for analysis results and analysis report
    .ignore: files not needed in analysis results
    .report_files: files needed for generate report
    '''
    _module = 'test'

    def run(self):
        ignore_files = config.module_file[self._module]['ignore_files']
        if 'pdf_files' in config.module_file[self._module]:
            pdf_report_files_pattern = config.module_file[self._module]['pdf_files']
            pdf_report_files = rsync_pattern_to_file(
                config.module_dir[self._module]['main'], pdf_report_files_pattern)
            pdf_report_ini = os.path.join(
                config.module_dir[self._module]['main'], '.report_files')
            write_obj_to_file(pdf_report_files, pdf_report_ini)
        with self.output().open('w') as ignore_files_inf:
            for each_file in ignore_files:
                ignore_files_inf.write('{}\n'.format(each_file))

    def output(self):
        return luigi.LocalTarget('{main_dir}/.ignore'.format(
            main_dir=config.module_dir[self._module]['main']
        ))


class cp_analysis_result(simple_task):

    _tag = 'cp_results'
    _module = 'test'
    _main_dir = config.module_dir[_module]['main']
    _result_dir = config.module_dir['result']['result']

    def run(self):
        _run_cmd = config.module_cmd['cp_results'].format(
            t=self)
        _process = envoy.run(_run_cmd)
        with self.output().open('w') as simple_task_log:
            simple_task_log.write(_process.std_err)
