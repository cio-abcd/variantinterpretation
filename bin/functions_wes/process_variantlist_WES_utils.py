# -*- coding: utf-8 -*-
def concatenate_https_clinvar(rs):
    """
    Concatenate https_clinvar link with rs number
    Function of function "clinar_link_list"

    Parameters
    ----------
    rs : pandas.core.series.Series

    Returns
    -------
    https_clinvar_link : List

    """
    return "https://www.ncbi.nlm.nih.gov/clinvar/?term="+rs


def unlist_https_clinvar(link):
    """
    Unlist result of function "concatenate_https_clinvar"
    Function of function "clinar_link_list"

    Parameters
    ----------
    link : List

    Returns
    -------
    i : str

    """
    for i in link:
        return i

def clinvar_link_list(link_lst, rs_idx, rs):
    """
    Generates a clinvar link using rs numbers

    Parameters
    ----------
    link_lst : empty List

    rs_idx : List of rs indices (obtained from pandas.core.series.Series with
                                 non-ordered indices)
    rs : pandas.core.series.Series

    Returns
    -------
    link_lst : List of https_clinvar_links

    """
    for i, idx in enumerate(rs_idx):

       if pd.isna(rs[rs_idx[i]]) == False:

            tmp_link = list(map(concatenate_https_clinvar,\
                                rs[rs_idx[i]].split(",")))
            tmp_link = unlist_https_clinvar(tmp_link)
            link_lst.append(tmp_link)

       else:
            link_lst.append(rs[rs_idx[i]])

    return link_lst
