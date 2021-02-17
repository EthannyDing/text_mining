import pandas as pd, os
from pathlib import Path

def length_ratio(sourceSeg, candidateSeg, category='word'):
    """Calculate the length ratio between source segments and candidate segments.
        sourceSeg: a list of numpy array of source segments.
        candidateSeg: a list of numpy array of candidate segments.
        category:
                1. 'word': calculate word length of both, get ratio.
                2. 'char': calculate character length of both, get ratio.

        return: a list of ratio value."""

    if category == 'word':
        ratios = [len(src.split())/len(cdd.split()) if len(src.split())/len(cdd.split()) <= 1
                  else len(cdd.split())/len(src.split())
                  for src, cdd in zip(sourceSeg, candidateSeg)]

    elif category == 'char':
        ratios = [len(src)/len(cdd) if len(src)/len(cdd) <= 1
                  else len(cdd)/len(src)
                  for src, cdd in zip(sourceSeg, candidateSeg)]

    else:
        raise Exception("Category not supported.")

    return ratios


def test_length_ratio():
    # print(Path.joinpath(Path(__file__).parent.parent, 'client', 'final_client_merge_dedup_cleaned.Matched.xlsx'))
    filePath = os.path.join(Path(os.path.abspath(__file__)).parent.parent.__str__(), 'client', 'final_client_merge_dedup_cleaned.Matched.xlsx')
    df = pd.read_excel(filePath)

    word_ratios = length_ratio(df['source'].to_numpy(dtype=str), df['Best_candidate_src'].to_numpy(dtype=str), category='word')
    char_ratios = length_ratio(df['source'].to_numpy(dtype=str), df['Best_candidate_src'].to_numpy(dtype=str), category='char')

    df['word ratio'] = word_ratios
    df['char ratio'] = char_ratios

    df.to_excel(filePath, header=True, index=None)


if __name__ == '__main__':

    test_length_ratio()
