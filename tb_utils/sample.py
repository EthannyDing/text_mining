import os, pandas as pd, codecs, sys
import random


def sample(input_file, output_file, sample_num=100, is_parallel=True, file_type='2txt'):
    """Sample texts from e.g. training data, TM, etc.
    Note: output file has to be an Excel file."""

    # print(input_file, output_file, sample_num, is_parallel, file_type)
    sample_num = int(sample_num)
    is_parallel = True if is_parallel == "True" else False
    # print(is_parallel)
    if is_parallel:

        if file_type == '2txt':
            with codecs.open(input_file[0], 'r') as f:
                eng_lines = f.readlines()
            with codecs.open(input_file[1], 'r') as f:
                fra_lines = f.readlines()

        elif file_type == 'excel':
            df_input = pd.read_excel(input_file)
            eng_lines = df_input["source"]
            fra_lines = df_input["target"]
        else:
            raise Exception("file format not supported.")

        data = list(zip(eng_lines, fra_lines))
        columns = ['src_sampled', 'tgt_sampled']

    else:
        if file_type == '2txt':
            with codecs.open(input_file, 'r') as f:
                data = f.readlines()

        elif file_type == 'excel':
            df_input = pd.read_excel(input_file)
            data = df_input[df_input.columns[0]]
            del df_input
        else:
            raise Exception("file format not supported.")
        columns = ['sampled']

    samples = random.sample(data, sample_num)
    df = pd.DataFrame(samples, columns=columns)
    df.to_excel(output_file, header=True, index=None)


if __name__ == '__main__':

    args = sys.argv[1:]
    sample(*args)
