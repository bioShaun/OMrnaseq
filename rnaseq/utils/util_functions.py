import glob


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