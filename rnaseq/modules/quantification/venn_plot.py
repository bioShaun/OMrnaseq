#! /usr/bin/env python
# coding=utf-8
import click
import sys
import os
import pandas as pd
from rnaseq.utils import config
from rnaseq.utils import venn
from rnaseq.utils.util_functions import save_mkdir
from rnaseq.utils.util_functions import write_obj_to_file


def output_plot(fig, out_prefix):
    png_file = '{p}.png'.format(p=out_prefix)
    pdf_file = '{p}.pdf'.format(p=out_prefix)
    fig.savefig(png_file, dpi=300)
    fig.savefig(pdf_file)
    fig.clear()


@click.command()
@click.option('-d', '--diff_dir', type=click.Path(exists=True), required=True,
              help='differential analysis directory.')
@click.option('-c', '--combination', type=click.STRING, required=True,
              help='venn plot combination, 2 ~ 5 Sets, seperated with ",".')
@click.option('-o', '--out_dir', type=click.Path(), required=True,
              help='output directory.')
def main(diff_dir, combination, out_dir):
    combination_list = combination.split(',')
    comb_num = len(combination_list)
    # check combination number, only support 2-5 combination to draw venn
    if comb_num < 2 or comb_num > 5:
        click.echo('Sets number error.\nSupported 2-5 sets venn plot.')
        sys.exit(1)

    # read diff-gene list
    gene_list = []
    diff_gene_sfx = config.file_suffix['diff_list']
    for each_com in combination_list:
        each_com_diff_genes = os.path.join(
            diff_dir, each_com, '{c}.ALL.{s}'.format(
                c=each_com, s=diff_gene_sfx))
        diff_df = pd.read_table(each_com_diff_genes, header=None, index_col=0)
        gene_list.append(diff_df.index)

    # draw venn, output 2 figs, one with logical numbers and the other without
    labels, col_set = venn.get_labels(gene_list, fill=['number', 'logic'])
    labels_simple, col_set = venn.get_labels(gene_list, fill=['number'])
    out_dir = os.path.join(out_dir, '_'.join(combination_list))
    save_mkdir(out_dir)
    venn_plot = getattr(venn, 'venn{n}'.format(n=comb_num))
    fig_detail, ax = venn_plot(labels, names=combination_list)
    venn_detail = os.path.join(out_dir, 'venn_plot.detail')
    output_plot(fig_detail, venn_detail)
    fig_simple, ax = venn_plot(labels_simple, names=combination_list)
    venn_simple = os.path.join(out_dir, 'venn_plot')
    output_plot(fig_simple, venn_simple)

    # output gene ids in each part of venn
    for each_part in col_set:
        out_file = os.path.join(out_dir, '{n}.txt'.format(n=each_part))
        write_obj_to_file(col_set[each_part], out_file)


if __name__ == '__main__':
    main()
