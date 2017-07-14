import glob
import pandas as pd
import os
import pandas.io.formats.excel

def rsync_pattern_to_file(from_dir, pattern_list):
    pattern_path_list = [
        '{0}/{1}'.format(from_dir, each_pattern) for each_pattern in pattern_list]
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
