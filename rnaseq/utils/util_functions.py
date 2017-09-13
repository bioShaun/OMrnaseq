#! /usr/bin/env python

from __future__ import division
import glob
import pandas as pd
import os
import pandas.io.formats.excel
from . import config
import sys
import envoy
import subprocess
from PIL import Image
from click import Option, UsageError


class MutuallyExclusiveOption(Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
        help = kwargs.get('help', '')
        if self.mutually_exclusive:
            ex_str = ', '.join(self.mutually_exclusive)
            kwargs['help'] = help + (
                ' NOTE: This argument is mutually exclusive with '
                ' arguments: [' + ex_str + '].'
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                "Illegal usage: `{}` is mutually exclusive with "
                "arguments `{}`.".format(
                    self.name,
                    ', '.join(self.mutually_exclusive)
                )
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx,
            opts,
            args
        )


def rsync_pattern_to_file(from_dir, pattern_list):
    pattern_path_list = ['{0}/{1}'.format(from_dir, each_pattern)
                         for each_pattern in pattern_list]
    file_path_list = []
    for each_path in pattern_path_list:
        file_path_list.extend(glob.glob(each_path))
    return [each.split('{}/'.format(from_dir))[1] for each in file_path_list]


def get_enrichment_data(enrichment_dir, plots_num=10):
    go_dir = os.path.join(enrichment_dir, 'go')
    compare_list = os.listdir(go_dir)
    pathway_plots = []
    for each_compare in compare_list:
        pathway_plots.extend(rsync_pattern_to_file(enrichment_dir, [
                             'kegg/{}/*ALL.pathway/*pathview.png'.format(
                                 each_compare)])[:10])
    go_enrich_table = glob.glob(
        '{}/go/*/*.ALL.go.enrichment.txt'.format(enrichment_dir))[0]
    go_enrich_plot = glob.glob(
        '{}/go/*/*go.enrichment.barplot.png'.format(enrichment_dir))[0]
    go_enrich_table_report = os.path.join(
        enrichment_dir, 'report.go.table.txt')
    go_enrich_plot_report = os.path.join(
        enrichment_dir, 'go.enrichment.barplot.png')
    dag_type = ['CC', 'MF', 'BP']
    for each_type in dag_type:
        each_go_dag_plot = glob.glob(
            '{0}/go/*/DAG/*ALL.{1}*png'.format(enrichment_dir, each_type))[0]
        each_go_dag_report_plot = os.path.join(
            enrichment_dir, '{}.GO.DAG.png'.format(each_type))
        os.system('cp {0} {1}'.format(
            each_go_dag_plot, each_go_dag_report_plot))
    os.system('cp {0} {1}'.format(go_enrich_plot, go_enrich_plot_report))
    os.system('cut -f1-7 {0} > {1}'.format(go_enrich_table,
                                           go_enrich_table_report))
    kegg_enrich_table = glob.glob(
        '{}/kegg/*/*.ALL.kegg.enrichment.txt'.format(enrichment_dir))[0]
    kegg_enrich_plot = glob.glob(
        '{}/kegg/*/*kegg.enrichment.barplot.png'.format(enrichment_dir))[0]
    kegg_enrich_table_report = os.path.join(
        enrichment_dir, 'report.kegg.table.txt')
    kegg_enrich_plot_report = os.path.join(
        enrichment_dir, 'kegg.enrichment.barplot.png')
    kegg_pathway_plot = glob.glob(
        '{}/kegg/*/*ALL.pathway/*pathview.png'.format(enrichment_dir))[0]
    kegg_pathway_report_plot = os.path.join(
        enrichment_dir, 'kegg.pathview.png')
    os.system('cut -f1-7 {0} > {1}'.format(kegg_enrich_table,
                                           kegg_enrich_table_report))
    os.system('cp {0} {1}'.format(kegg_enrich_plot, kegg_enrich_plot_report))
    os.system('cp {0} {1}'.format(kegg_pathway_plot, kegg_pathway_report_plot))
    repor_data = ['report.go.table.txt', 'report.kegg.table.txt',
                  'go.enrichment.barplot.png', 'kegg.enrichment.barplot.png',
                  'kegg.pathview.png']
    go_dag_plots = ['{}.GO.DAG.png'.format(each) for each in dag_type]
    repor_data.extend(go_dag_plots)
    repor_data.extend(pathway_plots)
    return repor_data


def write_obj_to_file(obj, fn, append=False):
    fh = open(fn, 'a' if append is True else 'w')
    if type(obj) is str:
        fh.write('%s\n' % obj)
    elif type(obj) is list or type(obj) is set:
        for item in obj:
            fh.write('%s\n' % item)
    elif type(obj) is dict:
        for key, val in obj.iteritems():
            fh.write('%s\t%s\n' % (key, val))
    else:
        raise TypeError('invalid type for %s' % obj)
    fh.close()


def txt_to_excel(txt_file, sheet_name='Sheet1'):
    pandas.io.formats.excel.header_style = None
    txt_df = pd.read_table(txt_file)
    txt_file_name = os.path.basename(txt_file)
    txt_file_dir = os.path.dirname(txt_file)
    txt_file_prefix = os.path.splitext(txt_file_name)[0]
    excel_file = os.path.join(txt_file_dir, '{}.xlsx'.format(txt_file_prefix))
    writer = pd.ExcelWriter(excel_file, engine='xlsxwriter', options={
                            'strings_to_urls': False})
    txt_df.to_excel(writer, sheet_name, index=False)
    writer.save()


def purge(pattern):

    def remove_one_pattern(pattern):
        for each_file in glob.glob(pattern):
            os.remove(each_file)

    if isinstance(pattern, str):
        remove_one_pattern(pattern)
    elif isinstance(pattern, list):
        for each_pattern in pattern:
            remove_one_pattern(each_pattern)
    else:
        print('wrong file pattern type. list or string')
        sys.exit(1)


def clean_logs(proj_dir, module, task=None):
    if module not in config.module_name:
        sys.exit('module [{m}] not available.'.format(module))
    module_name_list = config.module_name[module]
    pipe_log_dir = config.module_dir['_module_summary']['logs']
    remove_log_list = [
        '{dir}/{main}/.ignore'.format(
            dir=proj_dir, main=config.module_dir[module]['main']),
        '{dir}/{p_log}/pipe_{m}.cp_results.log'.format(
            dir=proj_dir, p_log=pipe_log_dir, m=module),
        '{dir}/{p_log}/pipe_all.analysis.log'.format(
            dir=proj_dir, p_log=pipe_log_dir)]

    if not task:
        return 0
    elif task == 'check':
        purge(remove_log_list)
        return 1
    elif task == 'all':
        module_index = 0
    elif task not in module_name_list:
        return 0
        print 'wrong re-run value.'
        print 're-run values: check, all, {modules}.'.format(
            modules=', '.join(module_name_list)
        )
        sys.exit(1)
    else:
        module_index = module_name_list.index(task)
    re_run_modules = module_name_list[module_index:]
    remove_log_list.extend(['{dir}/{log}/{name}.*log'.format(
        dir=proj_dir, log=config.module_dir[module]['logs'], name=name
    ) for name in re_run_modules])
    purge(remove_log_list)
    return 1


def nohuprun_cmd(cmd):
    cmd_list = envoy.expand_args(cmd)[0]
    subprocess.Popen(cmd_list, shell=False)


def add_prefix_to_filename(file_path, add_inf='pdf'):
    file_name = os.path.basename(file_path)
    file_dir = os.path.dirname(file_path)
    file_prefix, file_sufix = os.path.splitext(file_name)
    return os.path.join(
        file_dir, '{f}.{a}{s}'.format(
            f=file_prefix, a=add_inf, s=file_sufix))


def plot_resize(ori_size, target_size):
    factor_size1 = round(target_size[0] / ori_size[0], 2)
    factor_size2 = round(target_size[1] / ori_size[1], 2)
    factor_size = min(factor_size1, factor_size2)
    return [int(each * factor_size) for each in ori_size]


def resize_report_plot(report_dir):
    pdf_path = config.report_picture['path']
    pdf_size = config.report_picture['size']

    for pdf_file in pdf_path:
        pdf_file_path = pdf_path[pdf_file]
        each_plot_path = os.path.join(report_dir, pdf_file_path)
        if os.path.exists(each_plot_path):
            each_plot_resize_path = add_prefix_to_filename(each_plot_path)
            each_plot_img = Image.open(each_plot_path)
            each_plot_img_size = each_plot_img.size
            each_plot_pdf_size = pdf_size[pdf_file]
            each_plot_pdf_size = [int(each)
                                  for each in each_plot_pdf_size.split(',')]
            new_size = plot_resize(each_plot_img_size, each_plot_pdf_size)
            each_plot_img.resize(new_size).save(each_plot_resize_path)

    return 'finished resize plot'


def rename_result_dir(proj_dir, sample_inf, species):
    sample_df = pd.read_table(sample_inf, header=None)
    sample_num = len(sample_df)
    result_name = 'mRNA_{n}_{s}_analysis'.format(
        n=sample_num, s=species)
    default_result_name = config.module_dir['result']['main']
    old_result_dir = os.path.join(proj_dir, default_result_name)
    new_result_dir = os.path.join(proj_dir, result_name)
    os.rename(old_result_dir, new_result_dir)
    return new_result_dir


def pipe_default_para(proj_dir, max_worker=8):
    proj_dir_name = os.path.basename(proj_dir)
    proj_name_list = proj_dir_name.split('-')
    try:
        sample_num = proj_name_list[1]
    except IndexError:
        sample_num = None
    else:
        try:
            sample_num = int(sample_num)
        except ValueError:
            sample_num = None
    try:
        species = proj_name_list[2]
    except IndexError:
        species = None
    if sample_num and sample_num > max_worker:
        sample_num = max_worker
    return sample_num, species


def save_mkdir(path):
    if not os.path.isdir(path):
        os.makedirs(path)
