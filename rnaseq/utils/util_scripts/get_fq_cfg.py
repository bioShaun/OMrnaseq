import click
import os
import re


FASTQ_TEMPLATE = '{sample}_{readnumber}.fq.gz'


@click.command()
@click.argument(
    'fq_dir',
    type=click.Path(file_okay=False, exists=True),
    required=True
)
@click.argument(
    'fq_cfg',
    type=click.File('w'),
    required=True
)
@click.argument(
    'analysis_dir',
    type=click.Path(exists=False),
    required=True
)
@click.option(
    '-s',
    '--suffix',
    type=click.STRING,
    default='fq.gz',
    help='fastq file suffix.'
)
def main(fq_dir, fq_cfg,
         suffix, analysis_dir):
    fq_dir = os.path.abspath(fq_dir)
    fq_dict = dict()
    for root, dirs, files in os.walk(fq_dir):
        for each_file in files:
            if suffix in each_file:
                fq_name = os.path.basename(root)
                pattern = re.compile('([1,2]).{sf}'.format(sf=suffix))
                read_order = int(pattern.search(each_file).groups()[0])
                read_path = os.path.join(root, each_file)
                fq_dict.setdefault(fq_name, {})[read_order] = read_path

    analysis_dir = os.path.abspath(analysis_dir)
    for each_sample in fq_dict:
        each_sample_dir = os.path.join(analysis_dir,
                                       each_sample)
        os.makedirs(each_sample_dir)
        a_reads = list()
        for i in range(1, 3):
            a_read = os.path.join(each_sample_dir,
                                  FASTQ_TEMPLATE.format(sample=each_sample,
                                                        readnumber=i))
            r_read = fq_dict[each_sample][i]
            os.system('ln -s {rr} {ar}'.format(rr=r_read,
                                               ar=a_read))
            a_reads.append(a_read)
        fq_cfg.write('{sp}\t{r1}\t{r2}\n'.format(
            sp=each_sample,
            r1=a_reads[0],
            r2=a_reads[1]
        ))


if __name__ == '__main__':
    main()
