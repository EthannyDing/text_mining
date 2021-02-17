import pandas as pd
from collections import defaultdict


def summary_info_historic(summary_dir, summary_sheet='Summary', column="Province", province_id=' - Courts'):
    """obtain a dictionary where key is province and value is its codes from previously prepared summary file."""
    df = pd.read_excel(summary_dir, sheet_name=summary_sheet).fillna("")
    province_code = list(map(str, df[column])) + [""]
    courts = [str(c) for c in province_code if str(c).endswith(province_id)]
    summary_info = defaultdict(list)

    for court in courts:
        prov_court = court.replace(province_id, "").strip()
        summary_info[prov_court] = []
        index = province_code.index(court)
        index += 1  # skip "Code" element.
        while True:
            index += 1
            code = province_code[index].strip().upper()
            if code:
                summary_info[prov_court].append(code)
            else:
                break

    return summary_info


def summary_info_new(summary_dir, code_column='Code', province_column='Province'):
    """obtain a dictionary where key is province and value is its codes from newly crawled mainsection info.xlsx."""
    df = pd.read_excel(summary_dir)
    summary_info = defaultdict(list)

    # groupby dataframe and convert to list
    groupby_province = list(df[[code_column, province_column]].groupby([province_column]))
    for province, codes in groupby_province:
        for code in codes[code_column]:  # grouped urls
            # new_code = str(url).split('/')[-2].upper()
            summary_info[province.upper()].append(str(code))

    return summary_info


def check_incremental(historic_summary, new_summary):
    """Check if new summary info has new codes from each province.
       return dataframe: new_code, province"""
    assert set(historic_summary.keys()) == set(new_summary.keys()), "Provinces not equal."
    incremental_info = pd.DataFrame({'Code': [], "Province": []})
    for province in historic_summary.keys():
        historic_codes = set(historic_summary[province])
        new_codes = set(new_summary[province])
        diff_codes = new_codes.difference(historic_codes)
        if diff_codes:
            diff_df = pd.DataFrame({'Code': list(diff_codes), "Province": [province]*len(diff_codes)})
            incremental_info = pd.concat([incremental_info, diff_df])

    return incremental_info


def get_monolingual_legislation(historic_dir, historic_bilingual, outputExcel, bilingual_sheets):
    """Make subtraction of historic urls from bilingual urls to get historic monolingual urls."""
    historic_urls = pd.read_excel(historic_dir)['URL']
    print("{} total urls".format(len(historic_urls)))

    biFile = pd.ExcelFile(historic_bilingual)
    bi_dfs = pd.concat([biFile.parse(sheet) for sheet in bilingual_sheets])['URL'].tolist()
    print("{} bilingual urls".format(len(bi_dfs)))

    historic_monolingual = historic_urls[historic_urls.apply(lambda x: x not in bi_dfs)]
    print("{} monolingual urls".format(len(historic_monolingual)))
    historic_monolingual.to_excel(outputExcel, header=True, index=None)


def test_1():
    summary_dir = '/linguistics/ethan/Crawled_data/Canlii/summary/Historic_Courts_20201130.xlsx'
    summary_info = summary_info_historic(summary_dir, summary_sheet='Summary', column="Province", province_id='- Courts')

    print(summary_info)
    # print(summary_info.keys())

def test_2():
    summary_dir = '/linguistics/ethan/Crawled_data/Canlii/Canlii_20201130_crawl_2020/tribunal_info.xlsx'
    summary_info = summary_info_new(summary_dir, code_column='Code', province_column='Province')
    print(summary_info)

def test_3():
    historic_summary_dir = '/linguistics/ethan/Crawled_data/Canlii/summary/Historic_Tribunals_20201130.xlsx'
    new_summary_dir = '/linguistics/ethan/Crawled_data/Canlii/Canlii_20201130_crawl_2020/tribunal_info.xlsx'
    historic_summary = summary_info_historic(historic_summary_dir, summary_sheet='Summary', column="Province",
                                             province_id='- Boards and Tribunals')  # <-- change accordingly
    new_summary = summary_info_new(new_summary_dir, code_column='Code', province_column='Province')

    outputExcel = '/linguistics/ethan/Crawled_data/Canlii/summary/incremental/incremental_codes.tribunal.xlsx'
    incremental_info = check_incremental(historic_summary, new_summary)
    incremental_info.to_excel(outputExcel, header=True, index=None)

def test_get_monolingual_legislation():
    historic_dir = '/linguistics/ethan/Crawled_data/Canlii/ALL_historic_urls.legislation.xlsx'
    historic_bilingual = '/linguistics/ethan/Crawled_data/Canlii/BilingualExecutable_20201202/CanLII_Legislation_URLs_20201130.xlsx'
    outputExcel = '/linguistics/ethan/Crawled_data/Canlii/histotic_monolingual.legislation.xlsx'
    bilingual_sheets = ['Statutes_final', 'Regulations_final', 'AnnualStatutes_final']
    get_monolingual_legislation(historic_dir, historic_bilingual, outputExcel, bilingual_sheets)

if __name__ == '__main__':
    # test_1()
    # test_2()
    # test_3()
    test_get_monolingual_legislation()