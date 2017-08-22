import glob
import pandas as pd
import os
import pandas.io.formats.excel
from . import config
import sys
import envoy
import subprocess


def rsync_pattern_to_file(from_dir, pattern_list):
    pattern_path_list = ['{0}/{1}'.format(from_dir, each_pattern)
                         for each_pattern in pattern_list]
    file_path_list = []
    for each_path in pattern_path_list:
        file_path_list.extend(glob.glob(each_path))
    return [each.split('{}/'.format(from_dir))[1] for each in file_path_list]


def write_obj_to_file(obj, fn, append=False):
    fh = open(fn, 'a' if append is True else 'w')
    if type(obj) is str:
        fh.write('%s\n' % obj)
    elif type(obj) is list:
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
        return 0
    module_name_list = config.module_name[module]
    pipe_log_dir = config.module_dir['_module_summary']['logs']
    remove_log_list = ['{dir}/{main}/.ignore'.format(
        dir=proj_dir, main=config.module_dir[module]['main']),
        '{dir}/{p_log}/pipe_{m}.cp_results.log'.format(
            dir=proj_dir, p_log=pipe_log_dir, m=module
    )]

    if not task:
        return 0
    elif task == 'check':
        purge(remove_log_list)
        return 1
    elif task == 'all':
        module_index = 0
    elif task not in module_name_list:
        return 0
        # print 'wrong re-run value.'
        # print 're-run values: check, all, {modules}.'.format(
        #     modules=', '.join(module_name_list)
        # )
        # sys.exit(1)
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
