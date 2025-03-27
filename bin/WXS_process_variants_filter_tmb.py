#!/usr/bin/env python3

import pandas as pd
import argparse
from datetime import datetime
import re

# Using argparse for positinal arguments
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--vembrane_table", type=str)
parser.add_argument("-r", "--refseq_list", type=str)
parser.add_argument("-D", "--variant_DBi", type=str)
parser.add_argument("-o", "--outfile", type=str)
parser.add_argument("-rv", "--removed_variants", type=str)
parser.add_argument("-tmb", "--tmb_output", type=str)
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
print("Output_file_3:", args.tmb_output)

# Script used
print("Script: WXS_process_variants_filter_tmb.py")

# Get VEMBRANE_TABLE.out data
VEMBRANE_TABLE_OUT = args.vembrane_table
#VEMBRANE_TABLE_OUT = "4_FF_T1.tsv"
VEMBRANE_TABLE_OUT_data = pd.read_csv(VEMBRANE_TABLE_OUT, sep="\t",low_memory=False)

# Get PASS variants and others # not needed, since bcftools has filtered out the 
# others
#vs_PASS = []
#vs_other = []
#for vs_index, filter_status in enumerate(VEMBRANE_TABLE_OUT_data["FILTER"]):
#    if filter_status == "['PASS']":
#        vs_PASS.append(vs_index)
#    else:
#        vs_other.append(vs_index)
        
# PASS variants
#data_PASS = VEMBRANE_TABLE_OUT_data.loc[vs_PASS, :]

# Remove INTERGENIC_VARIANTS
vs_intergenic = []
vs_report = []
for ir_index, csq_consequence in enumerate(VEMBRANE_TABLE_OUT_data["CSQ_Consequence"]):
    if csq_consequence == "intergenic_variant":
        vs_intergenic.append(ir_index)
    else:
        vs_report.append(ir_index)
        
#vs_filter_intergenic = VEMBRANE_TABLE_OUT_data[VEMBRANE_TABLE_OUT_data["CSQ_Consequence"]=="intergenic_variant"]
#data_report = VEMBRANE_TABLE_OUT_data[VEMBRANE_TABLE_OUT_data["CSQ_Consequence"]!="intergenic_variant"]
        
# Report variants
data_report = VEMBRANE_TABLE_OUT_data.loc[vs_report, :]

# Removed variants
intergenic_variants = VEMBRANE_TABLE_OUT_data.loc[vs_intergenic, :]

# SINGLEsample

# Variants with AF>5%
#data_report_AF = data_report[data_report["allele_fraction"] >= 0.05]
#
# Remove variants
#data_below_AF = data_report[data_report["allele_fraction"] < 0.05]

# MULTIsample
# get col names Normal and Tumor sample
AF_colnames = data_report.loc[:, data_report.columns.str.startswith\
                   ("allele_fraction")].columns.tolist()

RD_colnames = data_report.loc[:, data_report.columns.str.startswith\
                   ("read_depth")].columns.tolist()
      
# Variants with AF>5%
data_report_AF = data_report[data_report[AF_colnames[1]] >= 0.05]

# Remove variants
data_below_AF = data_report[data_report[AF_colnames[1]] < 0.05]

# TMB calculation
# filter variants
intergenic_variants_AF = intergenic_variants[intergenic_variants\
                                            [AF_colnames[1]] >= 0.05]
    
intergenic_variants_AF_RD = intergenic_variants_AF[intergenic_variants_AF\
                                            [RD_colnames[1]] >= 30]
    
data_report_AF_RD = data_report_AF[data_report_AF\
                                            [RD_colnames[1]] >= 30]

# concat variants
variants_tmb_frames = [data_report_AF_RD, intergenic_variants_AF_RD]
variants_tmb = pd.concat(variants_tmb_frames)

# remove duplicates based on CHROM, POS, REF, ALT, AF_colnames[1], RD_colnames[1]
unique_variants_tmb = variants_tmb.drop_duplicates(
                      subset = ["CHROM", "POS", "REF", "ALT", AF_colnames[1],
                                RD_colnames[1]]).reset_index(drop=True)

#synonymous_variants = unique_variants_tmb[unique_variants_tmb\
#                                          ["CSQ_HGVSp"].str.contains(r'=', na=False)]
    
non_synonymous_variants = unique_variants_tmb[unique_variants_tmb\
                                          ["CSQ_Consequence"] != "synonymous_variant"]
# get SNV, DEL, INS
#variant_clases = set(non_synonymous_variants["CSQ_VARIANT_CLASS"].to_list())

TMB_snv =  non_synonymous_variants[non_synonymous_variants\
                                   ["CSQ_VARIANT_CLASS"] == "SNV"]
    
TMB_del =  non_synonymous_variants[non_synonymous_variants\
                                   ["CSQ_VARIANT_CLASS"] == "deletion"]
    
TMB_ins =  non_synonymous_variants[non_synonymous_variants\
                                   ["CSQ_VARIANT_CLASS"] == "insertion"]
    
TMB_sub =  non_synonymous_variants[non_synonymous_variants\
                                   ["CSQ_VARIANT_CLASS"] == "substitution"]

# count numbers
TMB_snv_final = len(TMB_snv)
TMB_snv_delins_final = len(TMB_snv) + len(TMB_del) + len(TMB_ins)

Regionsgroesse_MB = 3099.73 # 3099734149

# make dataframe
TMB = pd.DataFrame()

header_col = ["Anzahl TMB Mut. missense", "Anzahl TMB Mut. Missense + InDel", "Regionsgroesse [Mb]",\
              "TMB Missense", \
              "TMB Missense + InDel"]

for col in header_col:
    TMB [col] = ""
    
TMB.loc[0, "Anzahl TMB Mut. missense"] = TMB_snv_final
TMB.loc[0, "Anzahl TMB Mut. Missense + InDel"] = TMB_snv_delins_final
TMB.loc[0, "Regionsgroesse [Mb]"] = Regionsgroesse_MB
TMB.loc[0, "TMB Missense"] = round(TMB_snv_final/Regionsgroesse_MB, 2)
TMB.loc[0, "TMB Missense + InDel"] = round(TMB_snv_delins_final/Regionsgroesse_MB, 2)
    
TMB.to_csv(args.tmb_output, index=False) 


# Load RefSeq transcripts to list
transcript_list = args.refseq_list
#transcript_list = "12032025_use_in_wgs_pilot_refseq.txt"
RefSeq_NM = pd.read_csv(transcript_list)
RefSeq_NM_lst = RefSeq_NM["NM_RefSeq_final"].values.tolist()

# Check transcript input for " "
for RefSeq_idx in range(len(RefSeq_NM)):
    if ' ' in RefSeq_NM.loc[RefSeq_idx, "NM_RefSeq_final"]:
        raise ValueError('Space in transcript name! Please correct!')

# Reset indices
data_report_AF = data_report_AF.reset_index(drop="TRUE")

# Separate nan values from column "CSQ_Feature"
#nan_index = []
#valid_transcript_index = []
#for i in range(len(data_report_AF["CSQ_Feature"])):
#    if pd.isna(data_report_AF["CSQ_Feature"].loc[i]) == True:
#        nan_index.append(i)
#    else:
#        valid_transcript_index.append(i)
#
# variants with valid transcript
#variants = data_report_AF.loc[valid_transcript_index, :]
#
# intergenic variants
#nan_variants = data_report_AF.loc[nan_index , :]

# Reset indices
#variants= variants.reset_index()  

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
variants_valid  = variants_valid[~variants_valid["CSQ_HGVSc"].str.contains(r':n.')]

# Reset indices
variants_valid = variants_valid .reset_index(drop="TRUE")

# Exclude intron variants 
# rsv = refseq_variant
keep_idx = []
remove_idx = []
for rsv_idx, rsv in enumerate(variants_valid["CSQ_HGVSc"]):
    tmp_rsv = rsv.split(":c.")[1]
    
    # exclude e.g. NM.x:c.-... and NM.x:c+...
    if tmp_rsv.startswith("-") or tmp_rsv.startswith("+") or tmp_rsv.startswith("*"):
        remove_idx.append(rsv_idx) # exclude
        
    # exclude e.g. NM.x:c.10+100 (>100) and NM.x:c.10-100 (>100)
    elif (len(re.findall(r"[+]",tmp_rsv)) == 1 or \
        len(re.findall(r"[-]",tmp_rsv)) == 1) and \
        (not tmp_rsv.startswith("-") and not tmp_rsv.startswith("+")):
            if re.search(r"[+]",tmp_rsv):
                
                tmp0 = tmp_rsv.split("+")[1]
                tmp0_0 = re.findall(r"\d+", tmp0)[0]
                if int(tmp0_0) > 100:
                    remove_idx.append(rsv_idx) # exclude
                else:
                    keep_idx.append(rsv_idx) # keep
                    
            elif re.search(r"[-]",tmp_rsv):
                     
                tmp1 = tmp_rsv.split("-")[1]
                tmp1_1 = re.findall(r"\d+", tmp1)[0]
                if int(tmp1_1) > 100:
                    remove_idx.append(rsv_idx) # exclude
                else:
                    keep_idx.append(rsv_idx) # keep
            else:
                keep_idx.append(rsv_idx) # keep

    # exclude e.g. NM_003629.4:c.107-17070_107-17069delinsAT
    elif (len(re.findall(r"[+]",tmp_rsv)) == 2 or \
        len(re.findall(r"[-]",tmp_rsv)) == 2) and \
        (not tmp_rsv.startswith("-") and not tmp_rsv.startswith("+")) and \
            len(re.findall(r"[_]", tmp_rsv)) == 1:
                
                if re.search(r"[+]",tmp_rsv):
                    
                    tmp2 = tmp_rsv.split("+")
                    tmp3 = tmp2[1].split("_")[0] # No.1
                    tmp4 = re.findall(r"\d+", tmp2[2])[0] # No.2
                    if int(tmp3) and int(tmp4) > 100:
                        remove_idx.append(rsv_idx) # exclude
                    else:
                        keep_idx.append(rsv_idx) # keep
                              
                elif re.search(r"[-]",tmp_rsv):
                    
                    tmp5 = tmp_rsv.split("-")
                    tmp6 = tmp5[1].split("_")[0] # No.1
                    tmp7 = re.findall(r"\d+", tmp5[2])[0] # No.2
                    if int(tmp6) and int(tmp7) > 100:
                        remove_idx.append(rsv_idx) # exclude
                    else:
                        keep_idx.append(rsv_idx) # keep
                else:
                    keep_idx.append(rsv_idx) # keep
                        
    else:
        keep_idx.append(rsv_idx) # keep
     
# variants final
variants_final = variants_valid.loc[keep_idx, :]

# variants exlude
variants_exlude = variants_valid.loc[remove_idx , :] 

# Customizing table output
# multiply AF columns *100
variants_final.loc[:, variants_final.columns.str.startswith\
                   ("allele_fraction")] = variants_final.loc\
                   [:, variants_final.columns.str.startswith\
                   ("allele_fraction")].mul(100)

#final_variants.filter(regex=r'^allele_*', axis=1).mul(100)

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
variantDBi = pd.read_excel(args.variant_DBi)

variants_final_dbi = pd.merge(variants_final,\
                  variantDBi,\
                  left_on = ["rs_number"],\
                  right_on = ["name dbsnp_v151_ensembl_hg38_no_alt_analysis_set"],\
                  how = "left")

# get more columns singesample
#final_format = variants_final_dbi[["CHROM", "POS", "REF", "ALT", "FILTER",
#                               "allele_fraction","read_depth", "CSQ_VARIANT_CLASS", 
#                               "CSQ_Consequence", "CSQ_IMPACT", "CSQ_MANE_SELECT",
#                               "CSQ_MANE_PLUS_CLINICAL", "CSQ_SYMBOL",
#                               "CSQ_Feature", "NM-Nummer", "HGVSc", "HGVSp", "CSQ_EXON",
#                               "CSQ_INTRON", "CSQ_STRAND", "CSQ_DOMAINS", "CSQ_miRNA",
#                               "CSQ_SOMATIC", "CSQ_AF", "CSQ_MAX_AF", 
#                               "CSQ_gnomADe_AF", "CSQ_gnomADg_AF", "CSQ_CLIN_SIG",
#                               "CSQ_SIFT","CSQ_PolyPhen", "rs_number", "Wertung",
#                               "CSQ_PUBMED"]]
#
# Round AF to max 2 decimals
#final_format.loc[:,"allele_fraction"]  = final_format\
#                                   ["allele_fraction"].apply(lambda x: round(x,2))
#                                   
# Sort Frequency
#final = final_format.sort_values(by=["allele_fraction"], ascending=False)

# get more columns multisample
final_format = variants_final_dbi[["CHROM", "POS", "REF", "ALT", "FILTER",
                               AF_colnames[0], RD_colnames[0], AF_colnames[1], 
                               RD_colnames[1], "CSQ_VARIANT_CLASS", 
                               "CSQ_Consequence", "CSQ_IMPACT", "CSQ_MANE_SELECT",
                               "CSQ_MANE_PLUS_CLINICAL", "CSQ_SYMBOL",
                               "CSQ_Feature", "NM-Nummer", "HGVSc", "HGVSp", "CSQ_EXON",
                               "CSQ_INTRON", "CSQ_STRAND", "CSQ_DOMAINS", "CSQ_miRNA",
                               "CSQ_SOMATIC", "CSQ_AF", "CSQ_MAX_AF", 
                               "CSQ_gnomADe_AF", "CSQ_gnomADg_AF", "CSQ_CLIN_SIG",
                               "CSQ_SIFT","CSQ_PolyPhen", "rs_number", "Wertung",
                               "CSQ_PUBMED"]]

# Round AF to max 2 decimals
final_format.loc[:,AF_colnames[0]]  = final_format\
                                   [AF_colnames[0]].apply(lambda x: round(x,2))

final_format.loc[:,AF_colnames[1]]  = final_format\
                                   [AF_colnames[1]].apply(lambda x: round(x,2))

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
final.to_csv(args.outfile, sep="\t", index = False)
# save output for vcf_filter
#variants_for_vcf_filter = final[["CHROM","POS","REF","ALT"]]
#unique_variants_for_vcf_filter = variants_for_vcf_filter.drop_duplicates()
#unique_variants_for_vcf_filter.to_csv(args.outfile, sep="\t", header = False,
#                               index = False)

# save file removed
discarded_data = [intergenic_variants, data_below_AF, no_refseq_match_variants, 
                  hgvsc_nan, variants_exlude]
removed = pd.concat(discarded_data)
removed.to_excel(args.removed_variants, 
                 index = False, 
                 engine= None)

# Log information
print("--> Writing file for variants for oncokb and file for removed data to xlsx file: successful!")

# Getting current date and time for log information
date_time_now = datetime.now()

# dd/mm/YY H:M:S
dt_string = date_time_now.strftime("%d/%m/%Y %H:%M:%S")
print("End:", dt_string)
