#!/usr/bin/env python

from __future__ import print_function
import luigi
import pandas as pd
from luigi.util import requires, inherits
import os
from rnaseq.utils import config
from rnaseq.utils.util_functions import get_enrichment_data
from rnaseq.modules.base_module import prepare, simple_task
from rnaseq.modules.base_module import collection_task, cp_analysis_result
import inspect
import sys


script_dir, script_name = os.path.split(os.path.abspath(__file__))
UTIL_DIR = os.path.dirname(inspect.getfile(config))
MODULE, _ = os.path.splitext(script_name)
GOSEQ_R = os.path.join(script_dir, 'go_analysis.R')
EXTRACT_INF_PY = os.path.join(
    UTIL_DIR, 'util_scripts', 'extract_info_by_id.py')
KEGG_PATHWAY_PY = os.path.join(script_dir, 'kegg_pathview.py')
TREAT_KEGG_OUT = os.path.join(script_dir, 'treat_kegg_table.py')
ENRICH_PLOT = os.path.join(script_dir, 'enrich_barplot.R')


class Pubvar:
    _module = MODULE


class enrich_prepare(prepare, Pubvar):
    go = luigi.Parameter()
    gene_length = luigi.Parameter()
    kegg = luigi.Parameter()
    sp = luigi.Parameter()
    kegg_bg = luigi.Parameter(default="")


@requires(enrich_prepare)
class run_goseq(simple_task, Pubvar):

    _run_goseq_script = GOSEQ_R
    compare = luigi.Parameter()
    reg = luigi.Parameter()
    genes = luigi.Parameter()
    go_dir = config.module_dir[MODULE]['go']

    def get_tag(self):
        return '{t.compare}.{t.reg}'.format(t=self)


@requires(enrich_prepare)
class run_kobas(simple_task, Pubvar):

    _extract_inf_py = EXTRACT_INF_PY
    _treat_table_py = TREAT_KEGG_OUT
    compare = luigi.Parameter()
    reg = luigi.Parameter()
    genes = luigi.Parameter()
    blast_dir = config.module_dir[MODULE]['blast']
    kegg_dir = config.module_dir[MODULE]['kegg']

    def get_tag(self):
        return '{t.compare}.{t.reg}'.format(t=self)


@requires(run_kobas)
class run_pathway(run_kobas, Pubvar):

    _pathway_py = KEGG_PATHWAY_PY
    diff_dir = config.module_dir['quant']['diff']
    diff_sfx = config.file_suffix['diff_table']
    blast_dir = config.module_dir[MODULE]['blast']
    kegg_dir = config.module_dir[MODULE]['kegg']


@inherits(enrich_prepare)
class run_enrich_barplot(simple_task, Pubvar):

    compare = luigi.Parameter()
    _enrich_plot = ENRICH_PLOT
    go_dir = config.module_dir[MODULE]['go']
    kegg_dir = config.module_dir[MODULE]['kegg']
    diff_dir = config.module_dir['quant']['diff']

    # TODO MERGE TWO enrich module
    # def requires(self):
    #     gene_files_df = pd.read_table(self.gene_files, header=None)
    #     if len(gene_files_df.columns) == 1:
    #         gene_files_df.columns = ['path']

    #         def get_name(x):
    #             return os.path.splitext(os.path.basename(x))[0]

    #         gene_files_df.loc[:, 'name'] = map(get_name, gene_files_df.path)
    #         gene_files_df.loc[:, 'dirname'] = gene_files_df.loc[:, 'name']
    #     elif len(gene_files_df.columns) == 2:
    #         gene_files_df.columns = ['name', 'path']
    #         gene_files_df.loc[:, 'dirname'] = gene_files_df.loc[:, 'name']
    #     elif len(gene_files_df.columns) == 3:
    #         gene_files_df.columns = ['dirname', 'name', 'path']
    #     else:
    #         print("Wrong gene list file format!")
    #         print("----------------------------")
    #         print("1. Two column file: tab seperated, \
    #               first column is gene list name,  \
    #              second column is gene list path.")
    #         print("2. Or one column file: gene list path \
    #               (using gene list prefix as name)")
    #         print("3. Three column file: tab seperated, \
    #               first column is enrich dirname, \
    #               second column is gene list name and \
    #               third column is gene list path.")
    #         print("----------------------------")
    #         sys.exit(1)
    #     return [(run_goseq(go=self.go, topgo=self.topgo,
    #                        gene_length=self.gene_length, kegg=self.kegg,
    #                        sp=self.sp, proj_dir=self.proj_dir,
    #                        name=gene_files_df.name[each],
    #                        genes=gene_files_df.path[each]),
    #              run_kobas(go=self.go, topgo=self.topgo, kegg_bg=self.kegg_bg,
    #                        gene_length=self.gene_length, kegg=self.kegg,
    #                        sp=self.sp, proj_dir=self.proj_dir,
    #                        name=gene_files_df.name[each],
    #                        genes=gene_files_df.path[each])
    #              ) for each in gene_files_df.index]

    def requires(self):
        diff_dir = os.path.join(
            self.proj_dir, self.diff_dir
        )
        reg_list = ['ALL']
        reg_list.extend(['{g}-UP'.format(g=group)
                         for group in self.compare.split('_vs_')])
        diff_list_sfx = config.file_suffix['diff_list']
        diff_files = ['{_dir}/{t.compare}/{t.compare}.{r}.{sfx}'.format(
            _dir=diff_dir, t=self, r=reg, sfx=diff_list_sfx
        ) for reg in reg_list]
        return [(run_goseq(proj_dir=self.proj_dir, go=self.go,
                           gene_length=self.gene_length,
                           compare=self.compare, reg=r,
                           genes=diff_files[n], kegg=self.kegg,
                           sp=self.sp, kegg_bg=self.kegg_bg),
                 run_pathway(proj_dir=self.proj_dir, go=self.go,
                             topgo=self.topgo, gene_length=self.gene_length,
                             compare=self.compare, reg=r,
                             genes=diff_files[n], kegg=self.kegg,
                             sp=self.sp, kegg_bg=self.kegg_bg), )
                for n, r in enumerate(reg_list)]

    def get_tag(self):
        return self.compare


@inherits(enrich_prepare)
class enrich_collection(collection_task, Pubvar):

    diff_dir = config.module_dir['quant']['diff']
    enrich_dir = config.module_dir[MODULE]['main']

    def run_prepare(self):
        enrich_dir = os.path.join(self.proj_dir, self.enrich_dir)
        get_enrichment_data(enrich_dir)

    def requires(self):
        diff_dir = os.path.join(
            self.proj_dir, self.diff_dir
        )
        compare_name_list = os.listdir(diff_dir)
        return [run_enrich_barplot(proj_dir=self.proj_dir, go=self.go,
                                   topgo=self.topgo, kegg_bg=self.kegg_bg,
                                   gene_length=self.gene_length,
                                   kegg=self.kegg, sp=self.sp,
                                   compare=compare)
                for compare in compare_name_list]


@requires(enrich_collection)
class enrich_results(cp_analysis_result, Pubvar):
    proj_name = luigi.Parameter()
    main_dir = config.module_dir[Pubvar._module]['main']
    result_dir = config.module_dir['result']['result']
    report_data = config.module_dir['result']['report_data']


if __name__ == '__main__':
    luigi.run()
