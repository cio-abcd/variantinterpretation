#!/usr/bin/env python3

import pandas as pd
import argparse
from datetime import datetime

# Using argparse for positinal arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--onco_maf", type=str)
parser.add_argument("-o", "--annotated_outfile", type=str)
args = parser.parse_args()

# Getting current date and time for log information
date_time_now = datetime.now()

# dd/mm/YY H:M:S
dt_string = date_time_now.strftime("%d/%m/%Y %H:%M:%S")
print("Start:", dt_string)

# Process information
print("Input_oncokb_out:", args.onco_maf)
print("Output_file:", args.annotated_outfile)

# Script used
print("Script: WXS_annotation.py")

# OncoKB output data
UKB_ONCOKB_OUT_data = pd.read_csv(args.onco_maf, sep="\t",low_memory=False)

# Calculate End Position
# SNV: Start Postion == End Position (len(Reference_Allele)) == 1
# Deletion: Start Position + (len(Reference_Allele -1)) [(len(Reference_Allele)) > 1]
# Insertion/Duplication: Start Position +1

# find index of Start Position column
start_pos_index = UKB_ONCOKB_OUT_data.columns.get_loc("Start_Position")
end_position_index = start_pos_index + 1
UKB_ONCOKB_OUT_data.insert(end_position_index, "End_Position", "")

for i, pos in enumerate(UKB_ONCOKB_OUT_data["Start_Position"]):
    if UKB_ONCOKB_OUT_data.loc[i,"Reference_Allele"] in ["A", "C", "G", "T"] and \
        len(UKB_ONCOKB_OUT_data.loc[i,"Reference_Allele"]) == 1:
            UKB_ONCOKB_OUT_data.loc[i,"End_Position"] = UKB_ONCOKB_OUT_data.loc\
                [i,"Start_Position"]
    elif len(UKB_ONCOKB_OUT_data.loc[i,"Reference_Allele"]) > 1:
        tmp_end_position0 = len(UKB_ONCOKB_OUT_data.loc[i,"Reference_Allele"]) - 1
        UKB_ONCOKB_OUT_data.loc[i,"End_Position"] =  UKB_ONCOKB_OUT_data.\
            loc[i,"Start_Position"] + tmp_end_position0
    elif UKB_ONCOKB_OUT_data.loc[i,"Reference_Allele"] not in ["A", "C", "G", "T"]:
        tmp_end_position1 = len(UKB_ONCOKB_OUT_data.loc[i,"Reference_Allele"]) + 1
        UKB_ONCOKB_OUT_data.loc[i,"End_Position"] =  UKB_ONCOKB_OUT_data.\
            loc[i,"Start_Position"] + tmp_end_position1
            
# final wgs pilot output
final_columns = ["Chromosome", "Start_Position", "End_Position", "Reference_Allele",
                 "Tumor_Seq_Allele2", "allele_fractionWGS15198-23_N_1",
                 "read_depthWGS15198-23_N_1]", "allele_fractionWGS15198-23_T_1",
                 "read_depthWGS15198-23_T_1]", "CSQ_VARIANT_CLASS",
                 "CSQ_Consequence", "HUGO_SYMBOL", "NM-Nummer", "HGVSc", "HGVSp",
                 "CSQ_EXON", "CSQ_AF", "CSQ_MAX_AF", "CSQ_gnomADe_AF", "CSQ_gnomADg_AF",
                 "CSQ_CLIN_SIG", "ANNOTATED", "GENE_IN_ONCOKB", "VARIANT_IN_ONCOKB",
                 "MUTATION_EFFECT", "ONCOGENIC", "CSQ_SIFT", "CSQ_PolyPhen",
                 "rs_number", "Wertung"]

final_output = UKB_ONCOKB_OUT_data[final_columns]

# save file final
final_output.to_excel(args.annotated_outfile, index = False, engine = None)

# Log information
print("--> Writing file annotated_variants to xlsx file: successful!")

# Getting current date and time for log information
date_time_now = datetime.now()

# dd/mm/YY H:M:S
dt_string = date_time_now.strftime("%d/%m/%Y %H:%M:%S")
print("End:", dt_string)

        
  
    

