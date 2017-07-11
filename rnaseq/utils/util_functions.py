import glob
import luigi
import os
from . import config


<<<<<<< HEAD
class prepare_dir(luigi.Task):

    proj_dir = luigi.Parameter()
    _module = None

    def run(self):
        with self.output().open('w') as prepare_dir_log:
            for each_module in config.module_dir[self._module]:
                each_module_dir = os.path.join(
                    self.proj_dir, config.module_dir[self._module][each_module])
                config.module_dir[self._module][each_module] = each_module_dir
                try:
                    os.makedirs(each_module_dir)
                except OSError:
                    prepare_dir_log.write(
                        '{each_module_dir} has been built before.'.format(**locals()))

    def output(self):
        return luigi.LocalTarget('{t.proj_dir}/{log_dir}/prepare_dir.log'.format(
            t=self, log_dir=config.module_dir[self._module]['logs']))


=======
>>>>>>> 4e136c66d0d8b2f7604b5a1b2d3b063655e6f6a7
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
