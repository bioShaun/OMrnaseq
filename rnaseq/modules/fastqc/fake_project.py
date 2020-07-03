#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
import glob
import envoy
import random
import string
import itertools
import numpy as np
import pandas as pd
from pandas import DataFrame, Series
from rnaseq.utils import config
from rnaseq.utils.util_functions import save_mkdir

reload(sys)
sys.setdefaultencoding('utf-8')


R_BIN="/workspace/public/software/R/R-3.4.3/executable/bin/"

script_dir, script_name = os.path.split(os.path.abspath(__file__))
GC_PLOT_R = os.path.join(script_dir, 'gc_plot.R')
RQ_PLOT_R = os.path.join(script_dir, 'reads_quality_plot.R')
MAPPING_PLOT_R = os.path.join(script_dir, 'mapping_report.R')
SNP_PLOT_R = os.path.join(script_dir, 'snp_report.R')
VIOLIN_PLOT_R = os.path.join(script_dir, 'expression_boxplot.R')
PCA_PLOT_R = os.path.join(script_dir, 'PCA.R')
GC_TEST_DATA = os.path.join(script_dir, 'test_data', 'unstrand.gc.txt')
TEST_DATA_DIR = os.path.join(script_dir, 'test_data')
READS_QUAL_TEST_DATA = os.path.join(
    script_dir, 'test_data', 'reads_quality.txt')
MODULE = 'fastqc'


QC_DATA_SUMMARY_HEADER = [
    'sample_id',
    'reads_num',
    'reads_len',
    'data_size',
    'q30',
    'gc'
]

QC_DATA_OUT_HEADER = [
    'Sample_ID',
    'Reads_Number(M)',
    'Reads_Length',
    'Data_Size(G)',
    'Q30(%)',
    'GC(%)'
]


Q30_LOWER = 95
Q30_UPPER = 97
GC_LOWER = 45
GC_UPPER = 50
MAPPING_LOWER = 95
MAPPING_UPPER = 98


def generate_sample_prefix(letter_num=3):
    name_pool = itertools.combinations_with_replacement(
        string.ascii_uppercase, letter_num
    )
    return ''.join(random.choice(list(name_pool)))


def generate_sample_name(abbr, num):
    return ['{abbr}_{n:0>4d}'.format(abbr=abbr, n=n + 1)
            for n in range(num)]


def generate_sample_data(min_val, max_val, num, step=0.01):
    data_pool = np.arange(min_val, max_val, step)
    return np.random.choice(data_pool, num)


def data_size_upper(data_size, rel_size=0.2, abs_size=5):
    return data_size + max(data_size * rel_size, abs_size)


def generate_fake_gc_file(outfile, offset=0.1):
    example_df = pd.read_table(GC_TEST_DATA)
    random_num = Series(
        generate_sample_data(0, offset, len(example_df), step=0.001))
    example_df.loc[:, 'A'] = example_df.A + random_num
    example_df.loc[:, 'T'] = example_df.loc[:, 'T'] + random_num
    example_df.loc[:, 'C'] = example_df.C - random_num
    example_df.loc[:, 'G'] = example_df.G - random_num
    example_df.to_csv(outfile, sep='\t', index=False)
    return example_df


def generate_fake_rq_file(outfile, offset=0.05):
    example_df = pd.read_table(READS_QUAL_TEST_DATA)
    offset_series = Series(
        generate_sample_data(1 - offset,
                             1 + offset,
                             len(example_df))
    )
    example_df.loc[:, 'Proportion'] = example_df.Proportion * \
        offset_series
    example_df.to_csv(outfile, sep='\t', index=False)
    return example_df


def generate_fake_mapping_file(outdir, qc_df):
    mapping_dir = os.path.join(outdir, 'mapping')
    save_mkdir(mapping_dir)
    mapping_plot_file = os.path.join(mapping_dir,
                                     'mapping_plot.txt')
    mapping_table_file = os.path.join(mapping_dir,
                                      'mapping_table.txt')
    sample_num = len(qc_df)
    mapping_plot_dict = dict()
    mapping_plot_dict['unique_mapped_reads'] = generate_sample_data(
        MAPPING_LOWER * 0.95,
        MAPPING_UPPER * 0.95,
        sample_num)
    mapping_plot_dict['multiple_mapped_reads'] = generate_sample_data(
        MAPPING_LOWER * 0.05,
        MAPPING_UPPER * 0.05,
        sample_num
    )
    mapping_plot_df = DataFrame(mapping_plot_dict)
    mapping_plot_df.loc[:, 'total_reads'] = 100
    mapping_plot_df.loc[:, 'Sample'] = qc_df.loc[:, 'sample_id']
    mapping_plot_df.to_csv(
        mapping_plot_file, sep='\t', index=False,
        columns=['Sample', 'total_reads',
                 'unique_mapped_reads',
                 'multiple_mapped_reads'])
    mapping_plot_cmd = '{R_BIN}/Rscript {map_r} --mapping_stats {map_f} --out_dir {map_d}'.format(
        map_r=MAPPING_PLOT_R, map_f=mapping_plot_file,
        map_d=mapping_dir, R_BIN=R_BIN
    )
    envoy.run(mapping_plot_cmd)
    mapping_plot_df = mapping_plot_df.set_index('Sample')
    mapping_plot_df.loc[:, 'unmapped_reads'] = mapping_plot_df.total_reads - \
        mapping_plot_df.unique_mapped_reads - \
        mapping_plot_df.multiple_mapped_reads
    mapping_plot_df = mapping_plot_df.applymap(
        lambda x: '{x:.2f}%'.format(x=x))
    mapping_plot_df.to_csv(
        mapping_table_file, sep='\t',
        columns=['unique_mapped_reads',
                 'multiple_mapped_reads',
                 'unmapped_reads'])


def valid_go_dir(go_base):
    go_dir = random.choice(os.listdir(go_base))
    go_path = os.path.join(go_base, go_dir)
    go_table = glob.glob('{}/*ALL.go.enrichment.txt'.format(go_path))
    go_plot = glob.glob('{}/*go.enrichment.barplot.png'.format(go_path))
    go_dag = glob.glob('{}/DAG/*ALL.*.GO.DAG.png'.format(go_path))
    go_files = go_table + go_plot + go_dag
    if len(go_files) != 5:
        return valid_go_dir(go_base, go_dir_list)
    else:
        test_file = os.path.basename(go_table[0])
        test_name = test_file.split('.ALL.go.enrichment.txt')[0]
        return test_name


def fake_quant(outdir, sample_num, qc_df):
    quant_dir = os.path.join(outdir, 'quantification')
    save_mkdir(quant_dir)
    quant_file_dir = os.path.join(TEST_DATA_DIR, 'quant')
    quant_file = os.path.join(quant_file_dir, 'test.tpm.txt')
    quant_df = pd.read_csv(quant_file, sep='\t', index_col=0)
    test_sample = random.sample(quant_df.columns, sample_num)
    test_df = quant_df.loc[:, test_sample]
    test_df.columns = qc_df.sample_id
    test_file = os.path.join(quant_dir, 'exp.txt')
    test_df.to_csv(test_file, sep='\t')
    cmd_list = []
    cmd_list.append(
        '{R_BIN}/Rscript {violin_r} {exp_f} {od}'.format(
            violin_r=VIOLIN_PLOT_R,
            exp_f=test_file,
            od=quant_dir,
            R_BIN=R_BIN
        )
    )
    cmd_list.append(
        '{R_BIN}/Rscript {pca_r} {exp_f} {od}'.format(
            pca_r=PCA_PLOT_R,
            exp_f=test_file,
            od=quant_dir,
            R_BIN=R_BIN
        )
    )
    vol_dir = os.path.join(quant_file_dir, 'volcano')
    all_vol_plots = glob.glob('{}/*.png'.format(vol_dir))
    vol_plot = random.choice(all_vol_plots)
    cmd_list.append('cp {vol_p} {od}/volcano.png'.format(
        vol_p=vol_plot,
        od=quant_dir
    ))
    for cmd in cmd_list:
        envoy.run(cmd)


def fake_lnc(outdir):
    lnc_dir = os.path.join(outdir, 'lncrna')
    save_mkdir(lnc_dir)
    lnc_file_dir = os.path.join(TEST_DATA_DIR, 'lnc')
    cmd_list = []
    cmd_list.append('cp {lnc_fd}/lncRNA_classify.png {lnc_fd}/feelnc.png {od}'.format(
        lnc_fd=lnc_file_dir,
        od=lnc_dir
    ))
    for cmd in cmd_list:
        envoy.run(cmd)


def fake_go_file(outdir):
    enrich_dir = os.path.join(outdir, 'enrichment')
    save_mkdir(enrich_dir)
    go_file_dir = os.path.join(
        TEST_DATA_DIR, 'go')
    test_name = valid_go_dir(go_file_dir)
    cmd_list = []
    cmd_list.append(
        'cp {go}/{name}/{name}.ALL.go.enrichment.txt {od}/go.table.txt'.format(
            go=go_file_dir, name=test_name, od=enrich_dir
        )
    )
    # cmd_list.append(
    #     'cp {go}/{name}/{name}.go.enrichment.barplot.png {od}/go.barplot.png'.format(
    #         go=go_file_dir, name=test_name, od=enrich_dir
    #     )
    # )
    cmd_list.append(
        'cp {go}/{name}/DAG/{name}.ALL.BP.GO.DAG.png {od}/BP.DAG.png'.format(
            go=go_file_dir, name=test_name, od=enrich_dir
        )
    )
    cmd_list.append(
        'cp {go}/{name}/DAG/{name}.ALL.CC.GO.DAG.png {od}/CC.DAG.png'.format(
            go=go_file_dir, name=test_name, od=enrich_dir
        )
    )
    cmd_list.append(
        'cp {go}/{name}/DAG/{name}.ALL.MF.GO.DAG.png {od}/MF.DAG.png'.format(
            go=go_file_dir, name=test_name, od=enrich_dir
        )
    )
    for cmd in cmd_list:
        envoy.run(cmd)


def generate_fake_snp_file(species, qc_df, outdir):
    snp_dir = os.path.join(outdir, 'snp')
    save_mkdir(snp_dir)
    snp_num_out_file = os.path.join(outdir, 'snp', 'varNum.txt')
    snp_num_file = os.path.join(
        TEST_DATA_DIR, '{}.overall.varNum.txt'.format(species))
    snp_num_df = pd.read_table(snp_num_file)
    snp_num_df.columns = [each.strip() for each in snp_num_df.columns]
    sample_num = len(qc_df)
    random_num = Series(
        generate_sample_data(0.95 + 0.01 * sample_num,
                             1.05 + 0.01 * sample_num,
                             len(snp_num_df), step=0.1))
    snp_num_df.loc[:, 'Changes'] = snp_num_df.Changes * random_num
    snp_num_df.loc[:, 'Changes'] = snp_num_df.Changes.astype('int')
    snp_num_df.loc[:, 'Change_rate'] = snp_num_df.Length / snp_num_df.Changes
    snp_num_df.loc[:, 'Change_rate'] = snp_num_df.Change_rate.astype('int')
    snp_num_df.to_csv(snp_num_out_file, index=False, sep='\t')

    def random_snp_stats(snp_stats_name, outdir):
        snp_vartype_file = os.path.join(
            TEST_DATA_DIR, 'overall.{}.txt'.format(snp_stats_name))
        outfile = os.path.join(outdir, '{}.txt'.format(snp_stats_name))
        snp_vartype_df = pd.read_table(snp_vartype_file, usecols=[0, 1])
        random_num = Series(
            generate_sample_data(0.95, 1.05,
                                 len(snp_vartype_df),
                                 step=0.1)
        )
        snp_vartype_df.columns = [each.strip()
                                  for each in snp_vartype_df.columns]
        random_num = Series(
            generate_sample_data(0.95, 1.05,
                                 len(snp_vartype_df),
                                 step=0.1)
        )
        snp_vartype_df.loc[:, 'overall'] = snp_vartype_df.overall * random_num
        snp_vartype_df.loc[:, 'overall'] = snp_vartype_df.overall.astype('int')
        snp_vartype_df.to_csv(outfile, sep='\t', index=False)
    var_stats = ['varType', 'varRegion', 'varEffects']
    [random_snp_stats(stats_i, snp_dir) for stats_i in var_stats]
    plot_cmd = '{R_BIN}/Rscript {snp_r} --snp_stats_dir {snp_d}'.format(
        snp_r=SNP_PLOT_R, snp_d=snp_dir, R_BIN=R_BIN
    )
    envoy.run(plot_cmd)


def main(proj_dir, sample_num, data_size,
         project_name='测试报告', project_id='测试报告',
         company='onmath', name_abbr='',
         project_type='rna', species='wheat'):
    # prepare working dir
    qc_main_dir = os.path.join(proj_dir,
                               config.module_dir[MODULE]['main'])
    gc_dir = os.path.join(proj_dir,
                          config.module_dir[MODULE]['gc'])
    rq_dir = os.path.join(proj_dir,
                          config.module_dir[MODULE]['reads_quality'])
    map(save_mkdir, [gc_dir, rq_dir])

    # generate data information table
    qc_summary_file = os.path.join(qc_main_dir,
                                   'fastqc_general_stats.txt')
    data_summary_dict = dict()
    if not name_abbr:
        name_abbr = generate_sample_prefix()
    data_summary_dict['sample_id'] = generate_sample_name(
        name_abbr, sample_num)
    data_summary_dict['data_size'] = generate_sample_data(
        data_size, data_size_upper(data_size), sample_num
    )
    data_summary_dict['q30'] = generate_sample_data(Q30_LOWER,
                                                    Q30_UPPER,
                                                    sample_num)
    data_summary_dict['gc'] = generate_sample_data(GC_LOWER,
                                                   GC_UPPER,
                                                   sample_num,
                                                   step=1)
    data_summary_df = DataFrame(data_summary_dict)
    data_summary_df.loc[:, 'reads_num'] = data_summary_df.data_size * \
        1000 / 150
    data_summary_df.loc[:, 'reads_len'] = 'PE150'

    # generate gc plot data & plot
    gc_files = [os.path.join(gc_dir, '{each}.gc.txt'.format(each=each))
                for each in data_summary_df.sample_id]
    map(generate_fake_gc_file, gc_files)

    # generate reads quality data & plot
    rq_files = [os.path.join(rq_dir, '{each}.reads_quality.txt'.format(
        each=each
    )) for each in data_summary_df.sample_id]
    map(generate_fake_rq_file, rq_files)

    # generate mapping rate table
    if project_type in ['exome', 'reseq', 'rna', 'lnc']:
        generate_fake_mapping_file(qc_main_dir, data_summary_df)
        # generate snp data
        if project_type in ['exome', 'reseq', ]:
            generate_fake_snp_file(species, data_summary_df, qc_main_dir)
        elif project_type in ['rna', 'lnc']:
            fake_go_file(qc_main_dir)
            fake_quant(qc_main_dir, sample_num, data_summary_df)
            if project_type == 'lnc':
                fake_lnc(qc_main_dir)

    data_summary_df = data_summary_df.loc[:, QC_DATA_SUMMARY_HEADER]
    data_summary_df.columns = QC_DATA_OUT_HEADER
    data_summary_df.to_csv(qc_summary_file, sep='\t',
                           index=False, float_format='%.2f')

    # generate plots & report
    envoy.run('{R_BIN}/Rscript {gc_r} --gc_dir {gc_dir}'.format(
        gc_r=GC_PLOT_R, gc_dir=gc_dir, R_BIN=R_BIN
    ))
    envoy.run('{R_BIN}/Rscript {rq_r} --rq_dir {rq_dir}'.format(
        rq_r=RQ_PLOT_R, rq_dir=rq_dir, R_BIN=R_BIN
    ))
    envoy.run('qc_report -n {pn} -i {pi} -c {cp} -t {pt} {pd}'.format(
        pn=project_name, pi=project_id,
        cp=company, pd=qc_main_dir, pt=project_type))


if __name__ == '__main__':
    main()
