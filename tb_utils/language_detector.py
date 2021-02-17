import spacy
import langid
from spacy_langdetect import LanguageDetector
import numpy as np, pandas as pd
from sklearn.metrics import precision_score, recall_score, accuracy_score, f1_score
corpus_name = "en_core_web_lg"

def spacy_classifier(texts, lowercase=True, langs=['en', 'fr']):

    nlp = spacy.load(corpus_name)
    nlp.add_pipe(LanguageDetector(), name="language_detector", last=True)
    if lowercase:
        detected_langs = [langs[0] if nlp(str(text).lower())._.language['language'] == langs[0] else langs[1]
                          for text in texts]
    else:
        detected_langs = [langs[0] if nlp(str(text))._.language['language'] == langs[0] else langs[1]
                          for text in texts]

    return detected_langs

def langid_classifier(texts, lowercase=True, langs=['en', 'fr']):

    langid.set_languages(langs)
    if lowercase:
        detected_langs = [langid.classify(str(text).lower())[0] for text in texts]
    else:
        detected_langs = [langid.classify(str(text))[0] for text in texts]

    return detected_langs

def metrics(true, pred, labels):

    acc = accuracy_score(true, pred)
    pre = precision_score(true, pred, labels=labels, average=None)
    rec = recall_score(true, pred, labels=labels, average=None)
    f1 = f1_score(true, pred, labels=labels, average=None)

    return acc, pre, rec, f1

def evaluate():

    file = '/linguistics/ethan/training_data/LangDetectTest/sample2000.xlsx'
    output = "/linguistics/ethan/training_data/LangDetectTest/sample2000.res.xlsx"
    df = pd.read_excel(file)

    df["spacy_low_res"] = spacy_classifier(df["Sentence"], lowercase=True)
    df["spacy_norm_res"] = spacy_classifier(df["Sentence"], lowercase=False)

    df["langid_low_res"] = langid_classifier(df["Sentence"], lowercase=True)
    df["langid_norm_res"] = langid_classifier(df["Sentence"], lowercase=False)

    # df.to_excel(file, header=True, index=None)
    labels = ['en', 'fr']
    df_eval = pd.DataFrame({"Metrics": ["accuracy", "precision_en", "recall_en", "f1_en",
                                        "precision_fr", "recall_fr", "f1_fr"]})
    acc, pre, rec, f1 = metrics(df["TrueLang"], df["spacy_low_res"], labels)
    df_eval["spacy_low_classifier"] = [acc, pre[0], rec[0], f1[0], pre[1], rec[1], f1[1]]

    acc, pre, rec, f1 = metrics(df["TrueLang"], df["spacy_norm_res"], labels)
    df_eval["spacy_norm_classifier"] = [acc, pre[0], rec[0], f1[0], pre[1], rec[1], f1[1]]

    acc, pre, rec, f1 = metrics(df["TrueLang"], df["langid_low_res"], labels)
    df_eval["langid_low_classifier"] = [acc, pre[0], rec[0], f1[0], pre[1], rec[1], f1[1]]

    acc, pre, rec, f1 = metrics(df["TrueLang"], df["langid_norm_res"], labels)
    df_eval["langid_norm_classifier"] = [acc, pre[0], rec[0], f1[0], pre[1], rec[1], f1[1]]

    writer = pd.ExcelWriter(output)
    df.to_excel(writer, sheet_name="predictions", index=False)
    df_eval.to_excel(writer, sheet_name="evaluations", index=False)
    writer.save()


if __name__ == "__main__":

    evaluate()
