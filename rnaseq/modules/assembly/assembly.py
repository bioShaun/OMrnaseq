#!/usr/bin/env python

import luigi
from luigi.util import requires, inherits
import os
from rnaseq.utils import config
from rnaseq.modules.base_module import prepare, simple_task
import subprocess
from rnaseq.modules.base_module import collection_task

script_dir, script_name = os.path.split(os.path.abspath(__file__))
MODULE, _ = os.path.splitext(script_name)
ASSEMBLE_THREAD = 8
GENE_TR_MAP_PY = os.path.join(script_dir, 'get_gene_to_trans.py')


class assembly_prepare(prepare):

    _module = MODULE
    bam_dir = luigi.Parameter()
    gtf = luigi.Parameter(default='')
    genome_fa = luigi.Parameter()


@requires(assembly_prepare)
class assembly_stringtie_a(simple_task):
    '''
    assemble transcriptome using stringtie
    '''

    _module = MODULE
    _stringtie = config.module_software['stringtie']
    sample = luigi.Parameter()
    thread = ASSEMBLE_THREAD
    assemble_dir = config.module_dir['assembly']['assemble']

    def get_tag(self):
        return self.sample

    def treat_parameter(self):
        self.gtf = '-G {t.gtf}'.format(t=self)


@inherits(assembly_prepare)
class assembly_stringtie_m(simple_task):
    '''
    merge assembly results
    '''

    _module = MODULE
    sample_inf = luigi.Parameter()
    _stringtie = config.module_software['stringtie']
    assemble_dir = config.module_dir['assembly']['assemble']
    merge_dir = config.module_dir['assembly']['merge']
    merge_out = config.file_suffix['assembly']['merge_gtf']

    def treat_parameter(self):
        cmd = 'ls {t.proj_dir}/{t.assemble_dir}/*gtf > \
               {t.proj_dir}/{t.assemble_dir}/gtf.list'.format(t=self)
        subprocess.Popen(cmd, shell=True)
        self.gtf = '-G {t.gtf}'.format(t=self)

    def requires(self):
        sample_list = [each.strip().split()[1]
                       for each in open(self.sample_inf)]
        return [assembly_stringtie_a(sample=sample, bam_dir=self.bam_dir,
                                     gtf=self.gtf, proj_dir=self.proj_dir,
                                     ) for sample in sample_list]


@requires(assembly_stringtie_m)
class assembly_quant_prepare(simple_task):

    _module = MODULE
    _gffread = config.module_software['gffread']
    _kallisto = config.module_software['kallisto']
    _gene_tr_map_py = GENE_TR_MAP_PY
    merge_dir = config.module_dir['assembly']['merge']
    merge_gtf = config.file_suffix['assembly']['merge_gtf']
    merge_fa = config.file_suffix['assembly']['merge_fa']


if __name__ == '__main__':
    luigi.run()
