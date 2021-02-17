import codecs, pandas as pd
from configparser import ConfigParser
import psycopg2


class SearchPSQL:

    def __init__(self, configPath):

        cp = ConfigParser()
        cp.read(configPath)
        self.config = cp._sections['PostgreSQL']
        # self.segment_table = cp.get("PsqlTables", "segment_table")
        # self.website_table = cp.get("PsqlTables", "website_table")
        # self.file_table = cp.get("PsqlTables", "file_table")

        # The tables attribute has DB table name as key and its column names as values.
        self.tables = {"segments": cp.get("PsqlTables", "segment_table").split(","),
                       "website": cp.get("PsqlTables", "website_table").split(","),
                       "file": cp.get("PsqlTables", "file_table").split(","),
                       "ycc_domains": cp.get("PsqlTables", "ycc_domains_table").split(",")}

        self.src_corpus_path = cp.get("Training", "src_corpus_path")
        self.tgt_corpus_path = cp.get("Training", "tgt_corpus_path")

        self.srcLang = cp.get("Language", "source_lang")
        self.tgtLang = cp.get("Language", "target_lang")
        self.conn = None

    def connect(self):
        """connect with DB table"""
        self.conn = psycopg2.connect(**self.config)
        # print("Connection established successfully.")
        cursor = self.conn.cursor()

        return cursor

    def get_segment_records(self, additional_info):
        """Get corpus data used to index.
            additional_info: a list for information that a record in DB table needs other than
                             source language, target language"""
        with codecs.open(self.src_corpus_path, 'r') as f:
            src_lines = f.readlines()
        with codecs.open(self.tgt_corpus_path, 'r') as f:
            tgt_lines = f.readlines()

        data = []
        for src, tgt in zip(src_lines, tgt_lines):
            record = (self.srcLang, self.tgtLang, src.strip(), tgt.strip(), *additional_info)
            data.append(record)

        print("{} Records Created, ready to be imported to Segment Table.".format(len(data)))
        return data

    # def get_website_source_records(self, info):
    #     """Get website records"""
    #     pass
    #
    # def get_file_source_records(self, info):
    #     """Get file records"""
    #     pass

    def insert_records(self, table_name, data, include_pk=False):
        """insert data records into provided table."""

        cursor = self.connect()
        # # get columns of the table.
        # cursor.execute("SELECT * FROM {} LIMIT 0".format(table_name))
        # column_names = tuple([desc[0] for desc in cursor.description])
        # print(cursor.description)
        if include_pk:
            column_names = self.tables[table_name]  # remove first element id.
        else:
            column_names = self.tables[table_name][1:]  # remove first element id.
        columns = ", ".join(column_names)
        data_slot = ", ".join(["%s"] * len(column_names))
        insert_query = "INSERT INTO {} ({}) VALUES ({});".format(table_name, columns, data_slot)

        print(insert_query)
        print("\n")
        # print(data)
        for record in data:
            cursor.execute(insert_query, (*record, ))

        self.conn.commit()
        self.conn.close()
        print("{} Records added to PostgreSQL.".format(len(data)))

    def fetch_records(self, query):
        """fetch records from database table."""
        cursor = self.connect()
        cursor.execute(query)
        record = cursor.fetchone()
        # record = {key: value for key, value in zip(self.tables["segments"], record)}

        self.conn.commit()
        self.conn.close()

        return record


def test_insert_data():

    # data = [('eng', 'fra', 'add "single" quota from script', 'add single "quota from script"')]
    # column_names = ("source_lang", "target_lang", "source_text", "target_text")

    configPath = "./config/search.conf"
    sp = SearchPSQL(configPath)

    table_name = "segments"

    # # when inserting segments.
    additional_info = ("machine cleaned", "TM", 1, None, "last updates on January 2021.")
    data = sp.get_segment_records(additional_info)

    # # when insert ycc_domains
    # ycc_file = './config/ycc info.xlsx'
    # df = pd.read_excel(ycc_file)
    # data = [tuple(ycc) for ycc in df.iloc]

    # # when insert website
    # data = [("LD2://public/Training data/Training_Law_Fin_Gov_202010/Sedar/cleaned_202101",
    #          "Alexa", "28493524", "2021-01-11", "26", "low cleaned + remove filename and language mismatches")]

    sp.insert_records(table_name, data, include_pk=False)


def test_fetch_data():
    query = "SELECT * FROM searchdb WHERE id = 10"

    configPath = "./config/postgresql.conf"
    sp = SearchPSQL(configPath)
    res = sp.fetch_records(query)
    print(res)


if __name__ == "__main__":

    test_insert_data()
    # test_fetch_data()
