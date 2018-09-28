#!/usr/bin/env python

import luigi
import os
from rnaseq.utils import config
import envoy
from rnaseq.utils.util_functions import rsync_pattern_to_file
from rnaseq.utils.util_functions import write_obj_to_file, save_mkdir


class prepare(luigi.Task):

    proj_dir = luigi.Parameter()

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


class collection_task(luigi.Task):
    '''
    generate config file for analysis results and analysis report
    .ignore: files not needed in analysis results
    .report_files: files needed for generate report
    '''
    proj_dir = luigi.Parameter()

    def run_prepare(self):
        pass

    def run(self):
        self.run_prepare()
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
    proj_dir = luigi.Parameter()

    def mk_result_dir(self):
        result_dir = os.path.join(self.proj_dir,
                                  self.proj_name,
                                  self.result_dir)
        report_dir = os.path.join(self.proj_dir,
                                  self.proj_name,
                                  self.report_data)
        map(save_mkdir, [result_dir, report_dir])

    def run(self):
        if self.result_dir is not None:
            self.mk_result_dir()
        _run_cmd = config.module_cmd[self._tag].format(
            t=self)
        _process = envoy.run(_run_cmd)
        with self.output().open('w') as simple_task_log:
            simple_task_log.write(_process.std_err)
            # simple_task_log.write('test')
