import yaml
import os
from . import config
import sys
from omdatabase import species


SPECIES_KINGDOM = ('animal', 'plant')
species_list = []
config_path = os.path.dirname(os.path.realpath(__file__))
database_config = os.path.join(config_path, 'database.yaml')
organism_config = os.path.join(config_path, 'organism.yaml')
database_dir = config.database['genome']


def load_database_inf():
    if not os.path.exists(database_config):
        return refresh_database_inf()
    else:
        with open(database_config) as database_config_inf:
            return yaml.load(database_config_inf)


def refresh_database_inf():
    database_inf_dict = {}
    database_names = os.listdir(database_dir)
    for each_database in database_names:
        each_database_dir = os.path.join(database_dir, each_database)
        for root, dirs, files in os.walk(each_database_dir):
            root_name = os.path.basename(root)
            parent_name = os.path.basename(os.path.dirname(root))
            if root_name in SPECIES_KINGDOM:
                species_list.extend(dirs)
            if parent_name in species_list and root_name == 'annotation':
                database_inf_dict.setdefault(each_database, {})[
                    parent_name] = dirs
    with open(database_config, 'w') as database_config_inf:
        yaml.dump(database_inf_dict, database_config_inf)
    return database_inf_dict


def get_kegg_biomart_id(sp_latin):
    with open(organism_config) as organism_inf:
        kegg_map_dict = yaml.load(organism_inf)
    kegg_sp, biomart_sp = '', ''
    if sp_latin in kegg_map_dict:
        kegg_sp = kegg_map_dict[sp_latin]
    sp_latin_list = sp_latin.split('_')
    biomart_sp = '{0}{1}'.format(sp_latin_list[0][0], sp_latin_list[1])
    return kegg_sp, biomart_sp


class sepcies_annotation_path(object):
    def __init__(self, sp_database, sp_latin, sp_db_version=None):
        self.sp_latin = sp_latin
        self.sp_database = sp_database
        self.sp_db_version = sp_db_version
        self.kingdom = None
        self.kegg_abbr = None
        self.genome_fa = None
        self.gtf = None
        self.bedfile = None
        self.star_index = None
        self.transcript = None
        self.gene_tr = None
        self.goseq_ano = None
        self.topgo_ano = None
        self.gene_len = None
        self.kegg_blast = None
        self.transcript_index = None
        self.exists = True

    def check_database(self):
        database_inf_dict = load_database_inf()
        if self.sp_database not in database_inf_dict:
            sys.exit('Database {n} not found in database\
                      directory [{p}].'.format(
                n=self.sp_database, p=database_dir
            ))
        else:
            if not self.sp_latin:
                sys.exit('Species latin name is required.')
            else:
                if self.sp_latin not in database_inf_dict[self.sp_database]:
                    # sys.exit('Species [{n}] not found in \
                    #           database directory [{p}].'.format(
                    #     n=self.sp_latin, p=database_dir
                    # ))
                    self.exists = False
                else:
                    if not self.sp_db_version:
                        self.sp_db_version = 'current'
                    else:
                        vs = database_inf_dict[self.sp_database][self.sp_latin]
                        if self.sp_db_version not in vs:
                            # sys.exit('Database version {n} not in \
                            #           database directory [{p}].'.format(
                            #     n=self.sp_db_version, p=database_dir
                            # ))
                            self.exists = False
        _species = ' '.join(self.sp_latin.split('_'))
        my_sp_inf = species.Species(_species)
        self.kingdom = my_sp_inf.kingdom
        sp_database_dir = os.path.join(database_dir, self.sp_database,
                                       self.kingdom, self.sp_latin,
                                       self.sp_db_version)
        return sp_database_dir

    def get_anno_inf(self):
        sp_database_dir = self.check_database()

        def get_annotation_path(x):
            return os.path.join(sp_database_dir,
                                '{0}.{1}'.format(self.sp_latin, x))

        self.kegg_abbr = get_kegg_biomart_id(self.sp_latin)[0]
        if not self.kegg_abbr:
            self.kegg_abbr = 'ko'
        self.genome_fa = get_annotation_path('genome.fa')
        self.geneme_fai = get_annotation_path('genome.fa.fai')
        self.gtf = get_annotation_path('genome.gtf')
        self.bedfile = get_annotation_path('genome.bed')
        self.star_index = os.path.join(sp_database_dir, 'star_index')
        self.transcript = get_annotation_path('transcript.fa')
        self.transcript_index = get_annotation_path(
            'transcript.fa.kallisto_idx')
        self.gene_tr = get_annotation_path('gene_trans_map.txt')
        self.goseq_ano = get_annotation_path('go.txt')
        self.topgo_ano = get_annotation_path('go_gene_go.txt')
        self.gene_len = get_annotation_path('gene_length.txt')
        self.kegg_blast = get_annotation_path('gene.kegg.blasttab')
