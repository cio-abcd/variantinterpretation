#!/usr/bin/env python3

import argparse
from datetime import datetime
from pathlib import Path
import re
import os
import io
import sys
import logging

import pandas as pd

from refseq_list_03_02_2025 import transcript_list, transcript_list_header
from variantenliste22_12_15_restyled_csv import variant_list_csv

ONCOKB_ANNOTATE_TMP_FILE = 'oncokb_outfile'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stderr_handler = logging.StreamHandler(sys.stderr)
logger.addHandler(stderr_handler)

def cli():
    # Using argparse for positinal arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("vcf_type", type=str, choices=['singlesample','paired'])
    parser.add_argument("library_type", type=str, choices=['panel', 'wes','wgs'])
    #parser.add_argument("refseq_list", type=Path)
    #parser.add_argument("variant_DBi", type=Path)
    parser.add_argument("vembrane_table", type=Path)
    parser.add_argument("--removed_variants", type=Path)
    parser.add_argument("--tmb_output", type=Path)
    parser.add_argument("-o", "--outfile", type=Path)
    parser.add_argument("--annotated_outfile", type=Path)

    parser.add_argument("--use_oncokb_token", default=None, type=str)
    args = parser.parse_args()

    if args.vcf_type != 'paired':
        raise NotImplemented()
    if args.library_type not in ['wes','wgs']:
        raise NotImplemented()

    return args

def process_variants(args):
    logger.info(f'''
    starting wxs_process_variants
    Input_vembrane_table: {args.vembrane_table}
    Output_file_1: {args.outfile}
    Output_file_2: {args.removed_variants}
    Output_file_3: {args.tmb_output}
    Script: WXS_process_variants_filter.py
    ''')

    # Get VEMBRANE_TABLE.out data
    VEMBRANE_TABLE_OUT = args.vembrane_table
    VEMBRANE_TABLE_OUT_data = pd.read_csv(VEMBRANE_TABLE_OUT, sep="\t",low_memory=False)

    # Load RefSeq transcripts to list
    RefSeq_NM = pd.DataFrame(transcript_list, columns=transcript_list_header)
    RefSeq_NM_lst = RefSeq_NM["NM_RefSeq_final"].values.tolist()
    variantDBi = pd.read_csv(io.StringIO(variant_list_csv))

    # Remove INTERGENIC_VARIANTS
    vs_intergenic = []
    vs_report = []
    for ir_index, csq_consequence in enumerate(VEMBRANE_TABLE_OUT_data["CSQ_Consequence"]):
        if csq_consequence == "intergenic_variant":
            vs_intergenic.append(ir_index)
        else:
            vs_report.append(ir_index)

    # Report variants
    data_report = VEMBRANE_TABLE_OUT_data.loc[vs_report, :]

    # Removed variants
    intergenic_variants = VEMBRANE_TABLE_OUT_data.loc[vs_intergenic, :]

    # MULTIsample
    # get col names Normal and Tumor sample
    af_cols : list[bool] = data_report.columns.str.startswith("allele_fraction")

    err_str = f'''
    unexpected number of allele_fraction columns in tsv, {af_cols}
    expecting normally 2 (matched) or 1 (singlesample)
    but was {af_cols}
    '''

    if sum(af_cols) == 1:
        vcftype = 'singlesample'
    elif sum(af_cols) == 2:
        vcftype = 'matched'
    else:
        raise RuntimeError(err_str)

    AF_colnames = data_report.loc[:, data_report.columns.str.startswith("allele_fraction")].columns.tolist()
    RD_colnames = data_report.loc[:, data_report.columns.str.startswith("read_depth")].columns.tolist()

    # Variants with AF>5%
    data_report_AF = data_report[data_report[AF_colnames[1]] >= 0.05]
    data_below_AF = data_report[data_report[AF_colnames[1]] < 0.05]

    # TMB calculation
    # filter variants
    intergenic_variants_AF = intergenic_variants[intergenic_variants[AF_colnames[1]] >= 0.05]
    intergenic_variants_AF_RD = intergenic_variants_AF[intergenic_variants_AF[RD_colnames[1]] >= 30]
    data_report_AF_RD = data_report_AF[data_report_AF[RD_colnames[1]] >= 30]

    # concat variants
    variants_tmb_frames = [data_report_AF_RD, intergenic_variants_AF_RD]
    variants_tmb = pd.concat(variants_tmb_frames)

    # remove duplicates based on CHROM, POS, REF, ALT, AF_colnames[1], RD_colnames[1]
    unique_variants_tmb = variants_tmb.drop_duplicates(
                          subset = ["CHROM", "POS", "REF", "ALT", AF_colnames[1],
                                    RD_colnames[1]]).reset_index(drop=True)

    non_synonymous_variants = unique_variants_tmb[unique_variants_tmb["CSQ_Consequence"] != "synonymous_variant"]
    TMB_snv =  non_synonymous_variants[non_synonymous_variants["CSQ_VARIANT_CLASS"] == "SNV"]
    TMB_del =  non_synonymous_variants[non_synonymous_variants["CSQ_VARIANT_CLASS"] == "deletion"]
    TMB_ins =  non_synonymous_variants[non_synonymous_variants["CSQ_VARIANT_CLASS"] == "insertion"]
    TMB_sub =  non_synonymous_variants[non_synonymous_variants["CSQ_VARIANT_CLASS"] == "substitution"]

    # count numbers
    TMB_snv_final = len(TMB_snv)
    TMB_snv_delins_final = len(TMB_snv) + len(TMB_del) + len(TMB_ins)

    # TODO: calculate this from a bedfile
    if args.library_type == "wes":
        Regionsgroesse_MB = 30.16
    elif args.library_type == "wgs":
        Regionsgroesse_MB = 3099.73 # 3099734149
    else:
        raise ValueError("library_type value not valid! Please correct!")

    # make dataframe
    TMB = pd.DataFrame()

    header_col = ["Anzahl TMB Mut. missense", "Anzahl TMB Mut. Missense + InDel",
                  "Regionsgroesse [Mb]","TMB Missense","TMB Missense + InDel"]

    for col in header_col:
        TMB [col] = ""

    TMB.loc[0, "Anzahl TMB Mut. missense"] = TMB_snv_final
    TMB.loc[0, "Anzahl TMB Mut. Missense + InDel"] = TMB_snv_delins_final
    TMB.loc[0, "Regionsgroesse [Mb]"] = Regionsgroesse_MB
    TMB.loc[0, "TMB Missense"] = round(TMB_snv_final/Regionsgroesse_MB, 2)
    TMB.loc[0, "TMB Missense + InDel"] = round(TMB_snv_delins_final/Regionsgroesse_MB, 2)

    # Check transcript input for " "
    for RefSeq_idx in range(len(RefSeq_NM)):
        if ' ' in RefSeq_NM.loc[RefSeq_idx, "NM_RefSeq_final"]:
            raise ValueError('Space in transcript name! Please correct!')

    # Reset indices
    data_report_AF = data_report_AF.reset_index(drop="TRUE")
    variants = data_report_AF

    NM_idx = []
    no_refseq_match_idx = []
    for i in range(len(variants["CSQ_Feature"])):
        if variants["CSQ_Feature"][i].split(".")[0] in RefSeq_NM_lst:
            NM_idx.append(i)
        else:
            no_refseq_match_idx.append(i)

    # Filter variants accoriing to NM_idx list
    # Store result in new variable
    refseq_variants = variants.loc[NM_idx, :]

    # remove no_refseq_match
    no_refseq_match_variants = variants.loc[no_refseq_match_idx, :]

    # Reset indices
    refseq_variants = refseq_variants.reset_index(drop="TRUE")

    # Exlude nan values in HGVSc nomenclature
    # Separate nan values from column "CSQ_Feature"
    nan_index = []
    valid_index = []
    for i in range(len(refseq_variants["CSQ_HGVSc"])):
        if pd.isna(refseq_variants["CSQ_HGVSc"].loc[i]) == True:
            nan_index.append(i)
        else:
            valid_index.append(i)

    # variants with valid HGVSc nomenclature
    variants_valid = refseq_variants.loc[valid_index, :]

    # nan HGVSc nomencalure
    hgvsc_nan = refseq_variants.loc[nan_index , :]

    # exclude :n. variants
    variants_valid  = variants_valid[~variants_valid["CSQ_HGVSc"].str.contains(r':n.', regex=False)]

    # exclude nucleotides upsteam (5') of ATG-translation codon, see https://hgvs-nomenclature.org/stable/background/numbering/
    variants_valid  = variants_valid[~variants_valid["CSQ_HGVSc"].str.contains(r':c.-', regex=False)]
    # exclude nucleotides downsteam (3') of ATG-translation codon
    variants_valid  = variants_valid[~variants_valid["CSQ_HGVSc"].str.contains(r':c.*', regex=False)]
    # this is maybe actually incorrect:
    # i couldnt find c.+ in
    # variants_valid  = variants_valid[~variants_valid["CSQ_HGVSc"].str.contains(r':c.+')]

    # Reset indices
    variants_valid = variants_valid .reset_index(drop="TRUE")

    # heuristic, filter out variants that are too far inside an intron, as those are less interesting
    ALLOWED_DISTANCE_FROM_EXON = 200

    # NM_000.00:c. ...
    # regex = r'^NM_\d+\.\d+\:(?P<variant_type>c)\.(?P<e_pos1>\d+)(?P<i_pos1>[+-]\d+)?(?P<e_pos2>_\d+(?P<i_pos2>[+-]\d+)?)?([ACGT]>[ACGT])?$'
    regex = r'^NM_\d+\.\d+\:(?P<variant_type>c)\.(?P<e_pos1>\d+)(?P<i_pos1>[+-]\d+)?(?P<e_pos2>_\d+(?P<i_pos2>[+-]\d+)?)?(([AGTC]>[AGTC])|delins[AGTC]{2}|dup|del|ins[AGTC]+)?(inv|delins[ACTG]+)?$'
    pattern = re.compile(regex, flags=re.ASCII)

    def is_interesting_intron(rsv):
        match = pattern.fullmatch(rsv)
        if match is None:
            logger.warning(f'hgvs did not match regex pattern: {rsv}')
            return True
        md = match.groupdict()
        exon_pos1 = md['e_pos1']
        intron_offs1 = md['i_pos1']
        exon_pos2 = md['e_pos2']
        intron_offs2 = md['i_pos2']

        min_dist = None

        if intron_offs1:
            min_dist = abs(int(intron_offs1.removeprefix('-').removeprefix('+')))

        if intron_offs2:
            min_dist2 = abs(int(intron_offs2.removeprefix('-').removeprefix('+')))

        if intron_offs1 and intron_offs2:
            min_dist = min(min_dist, min_dist2)
        elif intron_offs2:
            min_dist = min_dist2

        if min_dist and min_dist > ALLOWED_DISTANCE_FROM_EXON:
            return False

        return True

    # Exclude intron variants
    # based on HGVS nomenclature, see: https://hgvs-nomenclature.org/stable/
    # rsv = refseq_variant
    keep_idx = []
    remove_idx = []
    for rsv_idx, rsv in enumerate(variants_valid["CSQ_HGVSc"]):
        keep = is_interesting_intron(rsv)
        if keep:
            keep_idx.append(rsv_idx) # keep
        else:
            remove_idx.append(rsv_idx) # exclude

    # variants final
    variants_final = variants_valid.loc[keep_idx, :]

    # variants exlude
    variants_exlude = variants_valid.loc[remove_idx , :]

    # Customizing table output
    # multiply AF columns *100
    new_val = variants_final.loc[:, variants_final.columns.str.startswith("allele_fraction")].mul(100)
    variants_final.loc[:, variants_final.columns.str.startswith("allele_fraction")] = new_val


    # Get NM only in new column NM-Nummer
    variants_final["NM-Nummer"] = ""
    for index_nm, NM_name in variants_final["CSQ_HGVSc"].items():
        if pd.isna(NM_name):
            variants_final.loc[index_nm, "NM-Nummer"] =  NM_name
        else:
            variants_final.loc[index_nm, "NM-Nummer"] = NM_name.split(":")[0]

    # Get HGVSc only in new column HGVSc
    variants_final["HGVSc"] = ""
    for index_c, NM_tr in variants_final["CSQ_HGVSc"].items():
        if pd.isna(NM_tr):
            variants_final.loc[index_c, "HGVSc"] =  NM_tr
        else:
            variants_final.loc[index_c, "HGVSc"] = NM_tr.split(":")[1]

    # Get HGVSp only in new column HGVSp
    variants_final["HGVSp"] = ""
    for index_p, NP in variants_final["CSQ_HGVSp"].items():
        if pd.isna(NP):
            variants_final.loc[index_p, "HGVSp"] =  NP
        else:
            variants_final.loc[index_p, "HGVSp"] = NP.split(":")[1]

    # Get rs numbers
    variants_final["rs_number"] = ""
    for index_rs, rs in variants_final["CSQ_Existing_variation"].items():

        if rs != "[]":
            for i in rs.split("'"):
                if i.startswith("rs"):
                    variants_final.loc[index_rs, "rs_number"] = i

    # Merge/join internal variantDB (variantDBi)
    # Change to current "Variantenliste" if needed
    variants_final_dbi = pd.merge(variants_final,
                      variantDBi,
                      left_on = ["rs_number"],
                      right_on = ["name dbsnp_v151_ensembl_hg38_no_alt_analysis_set"],
                      how = "left")

    # get more columns multisample
    final_format = variants_final_dbi[["CHROM", "POS", "REF", "ALT", "FILTER",
                                   AF_colnames[0], RD_colnames[0], AF_colnames[1],
                                   RD_colnames[1], "CSQ_VARIANT_CLASS",
                                   "CSQ_Consequence", "CSQ_IMPACT", "CSQ_BIOTYPE",
                                   "CSQ_MANE_SELECT", "CSQ_MANE_PLUS_CLINICAL", "CSQ_SYMBOL",
                                   "CSQ_Feature", "NM-Nummer", "HGVSc", "HGVSp", "CSQ_EXON",
                                   "CSQ_INTRON", "CSQ_STRAND", "CSQ_DOMAINS", "CSQ_miRNA",
                                   "CSQ_SOMATIC", "CSQ_AF", "CSQ_MAX_AF",
                                   "CSQ_gnomADe_AF", "CSQ_gnomADg_AF", "CSQ_CLIN_SIG",
                                   "CSQ_SIFT","CSQ_PolyPhen", "rs_number", "Wertung",
                                   "CSQ_PUBMED"]]

    # Round AF to max 2 decimals
    final_format.loc[:,AF_colnames[0]]  = final_format[AF_colnames[0]].apply(lambda x: round(x,2))
    final_format.loc[:,AF_colnames[1]]  = final_format[AF_colnames[1]].apply(lambda x: round(x,2))

    # Sort Frequency
    final = final_format.sort_values(by=[AF_colnames[1]], ascending=False)

    # save file for maf converting
    final = final.rename(columns={"CHROM": "Chromosome",
                                  "POS": "Start_Position",
                                  "REF": "Reference_Allele",
                                  "ALT": "Tumor_Seq_Allele2",
                                  "CSQ_SYMBOL": "HUGO_SYMBOL"})

    normal_id = (re.findall(r'(?<=allele_fraction)[WGS\d+\-]*', AF_colnames[0]))[0] + "_N_1"
    tumor_id = (re.findall(r'(?<=allele_fraction)[WGS\d+\-]*', AF_colnames[1]))[0] + "_T_1"

    final["Tumor_Sample_Barcode"] = tumor_id
    final["Matched_Norm_Sample_Barcode"] = normal_id
    final["NCBI_Build"] = "GRCh38"

    # save file removed
    discarded_data = [intergenic_variants, data_below_AF, no_refseq_match_variants,
                      hgvsc_nan, variants_exlude]
    removed = pd.concat(discarded_data)

    final.to_csv(args.outfile, sep="\t", index = False)
    TMB.to_csv(args.tmb_output, index=False)

    # shard table because some wgs have too many variants for reqular excel output
    def shard_table(table, shard_size=1_000_000):
        n_shards, mod = divmod(len(table),shard_size)
        if mod != 0:
            n_shards += 1

        n_shards = max(1, n_shards) # write empty table (shard_0) too, in case

        for i in range(n_shards):
            yield table[i*shard_size:(i+1)*shard_size]


    for shard_i, table_shard in enumerate(shard_table(removed)):
        out_path = Path(args.removed_variants)
        out_name_no_suffix = out_path.with_suffix('')
        out_name = out_name_no_suffix.with_suffix(f'.shard_{shard_i}.xlsx')
        table_shard.to_excel(str(out_name),index = False,engine= None)

    logger.info('Writing file for variants for oncokb and file for removed data to xlsx file: successful!')
    return final


# originally from https://github.com/oncokb/oncokb-annotator AGPL-3.0 license
# but is and will be totally replaced shortly

from AnnotatorCore import ( setsampleidsfileterfile
    , setcancerhotspotsbaseurl
    , setoncokbbaseurl
    , setoncokbapitoken
    , readCancerTypes
    , validate_oncokb_token
    , processalterationevents
    , QueryType
    , ReferenceGenome
    )


def run_oncokb_annotation(oncokb_token):
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger('MafAnnotator')

    stderr_handler = logging.StreamHandler(sys.stderr)
    log.addHandler(stderr_handler)
    log.info('running oncokb annotation')

    # set default values
    previous_result_file = ''
    input_clinical_file = ''
    sample_ids_filter = ''
    default_cancer_type = ''
    oncokb_api_url = ''
    annotate_hotspots = False
    cancer_hotspots_base_url = ''
    query_type = None
    include_descriptions = False

    input_file = args.outfile
    oncokb_api_bearer_token = oncokb_token
    default_reference_genome = 'GRCh38'
    output_file = ONCOKB_ANNOTATE_TMP_FILE

    docstr = (
        '\n'
        'MafAnnotator.py -i <input MAF file> -o <output MAF file> [-p previous results] [-c <input clinical file>] '
        '[-s sample list filter] [-t <default tumor type>] [-u oncokb-base-url] [-b oncokb api bear token] [-a] '
        '[-q query type] [-r default reference genome] [-d include descriptions]\n'
        'For definitions of the MAF format, please see https://docs.gdc.cancer.gov/Data/File_Formats/MAF_Format/\n\n'
        'Essential MAF columns for querying HGVSp_Short and HGVSp(case insensitive):\n'
        '    Hugo_Symbol: Hugo gene symbol\n'
        '    Tumor_Sample_Barcode: sample ID\n'
        '    HGVSp(query type: HGVSp): protein change in HGVSp format\n'
        '    HGVSp_Short(query type: HGVSp_Short): protein change in HGVSp format using 1-letter amino-acid codes\n'
        'Essential MAF columns for querying HGVSg(case insensitive):\n'
        '    Tumor_Sample_Barcode: sample ID\n'
        '    HGVSg: Genomic change in HGVSg format\n'
        'Essential MAF columns for querying genomic change(case insensitive):\n'
        '    Tumor_Sample_Barcode: sample ID\n'
        '    Chromosome: Chromosome number\n'
        '    Start_Position: Mutation start coordinate\n'
        '    End_Position: Mutation end coordinate\n'
        '    Reference_Allele: The plus strand reference allele at this position\n'
        '    Tumor_Seq_Allele1: Primary data genotype for tumor sequencing (discovery) allele\n'
        '    Tumor_Seq_Allele2: Tumor sequencing (discovery) allele 2\n'
        'Essential clinical columns:\n'
        '    SAMPLE_ID: sample ID\n'
        '    ONCOTREE_CODE: tumor type code from oncotree (http://oncotree.mskcc.org)\n'
        'Cancer type will be assigned based on the following priority:\n'
        '    1) ONCOTREE_CODE in clinical data file\n'
        '    2) ONCOTREE_CODE exist in MAF\n'
        '    3) default tumor type (-t)\n'
        'Query type only allows the following values (case-insensitive):\n'
        '    - HGVSp_Short\n'
        '      It reads from column HGVSp_Short or Alteration\n'
        '    - HGVSp\n'
        '      It reads from column HGVSp or Alteration\n'
        '    - HGVSg\n'
        '      It reads from column HGVSg or Alteration\n'
        '    - Genomic_Change\n'
        '      It reads from columns Chromosome, Start_Position, End_Position, Reference_Allele, Tumor_Seq_Allele1 and Tumor_Seq_Allele2  \n'
        'Reference Genome only allows the following values(case-insensitive):\n'
        '    - GRCh37\n'
        '      GRCh38\n'
        'Default OncoKB base url is https://www.oncokb.org.\n'
        )

    setoncokbapitoken(oncokb_api_bearer_token)
    cancertypemap = {}
    validate_oncokb_token()
    processalterationevents(input_file, output_file, previous_result_file, default_cancer_type,
                            cancertypemap, annotate_hotspots, query_type, default_reference_genome,
                            include_descriptions)

    log.info('done!')

def oncokb_stub_annotation(args, output_variants_df):
    ''' stub out oncokb annotation for non-proprietary use, generate a empty csv file '''
    for onkokb_added_column in ['ANNOTATED', 'GENE_IN_ONCOKB', 'VARIANT_IN_ONCOKB', 'MUTATION_EFFECT', 'ONCOGENIC']:
        output_variants_df[onkokb_added_column] = None

    output_variants_df.to_csv(ONCOKB_ANNOTATE_TMP_FILE, index=False,sep='\t' )


def annotation(args):
    logger.info('running wxs final annotation')
    # previously in WXS_annotation.py
    onco_maf = ONCOKB_ANNOTATE_TMP_FILE
    # OncoKB output data
    UKB_ONCOKB_OUT_data = pd.read_csv(onco_maf, sep="\t",low_memory=False)

    # Calculate End Position
    # SNV: Start Postion == End Position (len(Reference_Allele)) == 1
    # Deletion: Start Position + (len(Reference_Allele -1)) [(len(Reference_Allele)) > 1]
    # Insertion/Duplication: Start Position +1

    # find index of Start Position column
    start_pos_index = UKB_ONCOKB_OUT_data.columns.get_loc("Start_Position")
    end_position_index = start_pos_index + 1
    UKB_ONCOKB_OUT_data.insert(end_position_index, "End_Position", "")

    for i, pos in enumerate(UKB_ONCOKB_OUT_data["Start_Position"]):
        if UKB_ONCOKB_OUT_data.loc[i,"Reference_Allele"] in ["A", "C", "G", "T"] and len(UKB_ONCOKB_OUT_data.loc[i,"Reference_Allele"]) == 1:
                UKB_ONCOKB_OUT_data.loc[i,"End_Position"] = UKB_ONCOKB_OUT_data.loc[i,"Start_Position"]
        elif len(UKB_ONCOKB_OUT_data.loc[i,"Reference_Allele"]) > 1:
            tmp_end_position0 = len(UKB_ONCOKB_OUT_data.loc[i,"Reference_Allele"]) - 1
            UKB_ONCOKB_OUT_data.loc[i,"End_Position"] =  UKB_ONCOKB_OUT_data.loc[i,"Start_Position"] + tmp_end_position0
        elif UKB_ONCOKB_OUT_data.loc[i,"Reference_Allele"] not in ["A", "C", "G", "T"]:
            tmp_end_position1 = len(UKB_ONCOKB_OUT_data.loc[i,"Reference_Allele"]) + 1
            UKB_ONCOKB_OUT_data.loc[i,"End_Position"] =  UKB_ONCOKB_OUT_data.loc[i,"Start_Position"] + tmp_end_position1

    # MULTIsample
    # get col names Normal and Tumor sample
    AF_colnames = UKB_ONCOKB_OUT_data.loc[:, UKB_ONCOKB_OUT_data.columns.str.startswith("allele_fraction")].columns.tolist()

    RD_colnames = UKB_ONCOKB_OUT_data.loc[:, UKB_ONCOKB_OUT_data.columns.str.startswith("read_depth")].columns.tolist()

    final_columns = ["Chromosome", "Start_Position", "End_Position", "Reference_Allele",
                     "Tumor_Seq_Allele2", AF_colnames[0], RD_colnames[0], AF_colnames[1],
                     RD_colnames[1], "CSQ_VARIANT_CLASS", "CSQ_BIOTYPE",
                     "CSQ_Consequence", "HUGO_SYMBOL", "NM-Nummer", "HGVSc", "HGVSp",
                     "CSQ_EXON", "CSQ_AF", "CSQ_MAX_AF", "CSQ_gnomADe_AF", "CSQ_gnomADg_AF",
                     "CSQ_CLIN_SIG", "ANNOTATED", "GENE_IN_ONCOKB", "VARIANT_IN_ONCOKB",
                     "MUTATION_EFFECT", "ONCOGENIC", "CSQ_SIFT", "CSQ_PolyPhen",
                     "rs_number", "Wertung"]

    final_output = UKB_ONCOKB_OUT_data[final_columns]
    final_output.to_excel(args.annotated_outfile, index = False, engine = None)
    logger.info('Writing file annotated_variants to xlsx file: successful!')


args = cli()
output_variants_df = process_variants(args)
if args.use_oncokb_token is not None:
    run_oncokb_annotation(args.use_oncokb_token)
else:
    oncokb_stub_annotation(args, output_variants_df)
annotation(args)
