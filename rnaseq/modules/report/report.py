#!/usr/bin/env python

import luigi
from rnaseq.utils import config
from pathlib import PurePath
from rnaseq.utils.util_functions import resize_report_plot
import envoy


class generate_report(luigi.Task):

    proj_name = luigi.Parameter()
    proj_dir = luigi.Parameter()

    def run(self):
        # adjust plot size for report
        self.result_dir = PurePath(self.proj_dir) / self.proj_name
        self.report_dir = self.result_dir / \
            config.module_dir['result']['report_dir']
        report_data_path = self.result_dir / \
            config.module_dir['result']['report_data']
        self.report_file = self.report_dir / \
            config.module_dir['result']['report_file']
        resize_report_plot(str(report_data_path))
        # generate report & clean report dir
        report_cmd = config.module_cmd['report']['generate_report']
        report_cmd = report_cmd.format(t=self)
        envoy.run(report_cmd)

    def output(self):
        report_file = PurePath(self.proj_dir) / self.proj_name / \
            config.module_dir['result']['report_file']
        return luigi.LocalTarget('{}'.format(report_file))
