#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import argparse
import functions_wes.process_variantlist_WES_utils as fp
from datetime import datetime

# Using argparse for positinal arguments
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--vembrane_table", type=str)
parser.add_argument("-r", "--refseq_list", type=str)
parser.add_argument("-D", "--variant_DBi", type=str)
parser.add_argument("-o", "--outfile", type=str)
parser.add_argument("-rv", "--removed_variants", type=str)
args = parser.parse_args()

# Getting current date and time for log information
date_time_now = datetime.now()

# dd/mm/YY H:M:S
dt_string = date_time_now.strftime("%d/%m/%Y %H:%M:%S")
print("Start:", dt_string)

# Process information
print("Input_vembrane_table:", args.vembrane_table)
print("Output_file_1:", args.outfile)
print("Output_file_2:", args.removed_variants)

# Script used
print("Script: WES_varianten_v1_unix.py")

# Get VEMBRANE_TABLE.out data
VEMBRANE_TABLE_OUT = args.vembrane_table
VEMBRANE_TABLE_OUT_data = pd.read_table(VEMBRANE_TABLE_OUT, low_memory=False)

# Get PASS variants and others
vs_PASS = []
vs_other = []
for vs_index, filter_status in enumerate(VEMBRANE_TABLE_OUT_data["FILTER"]):
    if filter_status == "['PASS']":
        vs_PASS.append(vs_index)
    else:
        vs_other.append(vs_index)

# PASS variants
data_PASS = VEMBRANE_TABLE_OUT_data.loc[vs_PASS, :]

# other variants/removed variants
removed_variants = VEMBRANE_TABLE_OUT_data.loc[vs_other, :]

# write file removed variants
removed_variants.to_excel(args.removed_variants, \
                            index = False, \
                             engine= None)

# Load WES RefSeq transcripts to list
transcript_list = args.refseq_list
RefSeq_NM = pd.read_excel(transcript_list)
RefSeq_NM_lst = RefSeq_NM["NM_RefSeq_final"].values.tolist()

# Check transcript input for " "
for RefSeq_idx in range(len(RefSeq_NM)):
    if ' ' in RefSeq_NM.loc[RefSeq_idx, "NM_RefSeq_final"]:
      raise ValueError('Space in transcript name! Please correct!')

# Reset indices
data_PASS = data_PASS.reset_index()

# Separate nan values from column "CSQ_Feature"
nan_index = []
valid_transcript_index = []
for i in range(len(data_PASS["CSQ_Feature"])):
    if pd.isna(data_PASS["CSQ_Feature"].loc[i]) == True:
        nan_index.append(i)
    else:
        valid_transcript_index.append(i)

# variants with valid transcript
variants = data_PASS.loc[valid_transcript_index, :]

# intergenic variants
intergenic_variants = data_PASS.loc[nan_index , :]

# Reset indices
variants= variants.reset_index()

# Get index of rows presented in WES RefSeq list
NM_idx = []
for i in range(len(variants["CSQ_Feature"])):
    if variants["CSQ_Feature"][i].split(".")[0] in RefSeq_NM_lst:
        NM_idx.append(i)

# Filter variants accoriing to NM_idx list
# Store result in new variable
refseq_variants = variants.loc[NM_idx, :]

# concatentate variants with intergenic variants
concatenated_variants = [refseq_variants, intergenic_variants]

# concatenate discarded/removed clc_data variants
final_variants = pd.concat(concatenated_variants)

# Customizing table output
# multiply AF columns *100
final_variants.loc[:, final_variants.columns.str.startswith\
                   ("allele_fraction")] = final_variants.loc\
                   [:, final_variants.columns.str.startswith\
                   ("allele_fraction")].mul(100)

#final_variants.filter(regex=r'^allele_*', axis=1).mul(100)

# Get HGVSc only in new column HGVSc
for index_c, NM_tr in final_variants["CSQ_HGVSc"].items():
    if pd.isna(NM_tr):
        final_variants.loc[index_c, "HGVSc"] =  NM_tr
    else:
        final_variants.loc[index_c, "HGVSc"] = NM_tr.split(":")[1]

# Get HGVSp only in new column HGVSp
for index_p, NP in final_variants["CSQ_HGVSp"].items():
    if pd.isna(NP):
        final_variants.loc[index_p, "HGVSp"] =  NP
    else:
        final_variants.loc[index_p, "HGVSp"] = NP.split(":")[1]

# Get rs numbers
for index_rs, rs in final_variants["CSQ_Existing_variation"].items():

    if rs != "[]":
        for i in rs.split("'"):
            if i.startswith("rs"):
                final_variants.loc[index_rs, "rs_number"] = i
    else:
        final_variants.loc[index_rs, "rs_number"] = rs

# Merge/join internal variantDB (variantDBi)
# Change to current "Variantenliste" if needed
variantDBi = pd.read_excel(args.variant_DBi)

final_variants = pd.merge(final_variants,\
                  variantDBi,\
                  left_on = ["rs_number"],\
                  right_on = ["name dbsnp_v151_ensembl_hg38_no_alt_analysis_set"],\
                  how = "left")

# Generate clinvar Link and add to data
# Add column "Clinvar_Link" and generate link
final_variants["Clinvar_Link"] = ""
rs = final_variants["rs_number"]
rs_idx = rs.index.tolist()
link_lst = []

# Get clinvar https list
final_variants["Clinvar_Link"] = fp.clinvar_link_list(link_lst,\
                                 rs_idx, rs)

# Log information
print("--> Processing Vembrane table out: successful!")

# get col names Normal and Tumor sample
AF_colnames = final_variants.loc[:, final_variants.columns.str.startswith\
                   ("allele_fraction")].columns.tolist()

RD_colnames = final_variants.loc[:, final_variants.columns.str.startswith\
                   ("read_depth")].columns.tolist()

# Get comprehensive output format
final_format = final_variants[["CHROM", "POS", "REF", "ALT", "FILTER",
                               "CSQ_VARIANT_CLASS", AF_colnames[0],
                               AF_colnames[1], RD_colnames[0], RD_colnames[1],
                               "CSQ_Consequence", "CSQ_IMPACT", "CSQ_MANE_SELECT",
                               "CSQ_MANE_PLUS_CLINICAL", "CSQ_SYMBOL",
                               "CSQ_Feature", "HGVSc", "HGVSp", "CSQ_EXON",
                               "CSQ_INTRON", "CSQ_STRAND", "CSQ_DOMAINS", "CSQ_miRNA",
                               "CSQ_SOMATIC", "CSQ_AF", "CSQ_MAX_AF", 
                               "CSQ_gnomADe_AF", "CSQ_gnomADg_AF", "CSQ_CLIN_SIG",
                               "CSQ_SIFT","CSQ_PolyPhen", "rs_number", "Wertung",
                               "Clinvar_Link", "CSQ_PUBMED"]]

# Round AF to max 2 decimals
final_format.loc[:,AF_colnames[0]]  = final_format\
                                   [AF_colnames[0]].apply(lambda x: round(x,2))

final_format.loc[:,AF_colnames[1]]  = final_format\
                                   [AF_colnames[1]].apply(lambda x: round(x,2))

# Sort Frequency
final = final_format.sort_values(by=[AF_colnames[1]], ascending=False)

# Add "submit" and "Interpretation" column
final.insert(loc=31, column="submit", value="-")
final.insert(loc=32, column="Interpretation", value="-")

# Save file
final.to_excel(args.outfile, \
                            index = False, \
                             engine= None)
# Log information
print("--> Writing data to xlsx output files: successful!")

# Getting current date and time for log information
date_time_now = datetime.now()

# dd/mm/YY H:M:S
dt_string = date_time_now.strftime("%d/%m/%Y %H:%M:%S")
print("End:", dt_string)
