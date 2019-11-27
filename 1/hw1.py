import xml.etree.ElementTree as ET
from collections import defaultdict
import csv
import random

forms = defaultdict(list)
freqs = defaultdict(int)
dictionary = {}
pst = ["S", "A", "V", "PR", "CONJ", "ADV", "NI"]
posts = {"мн.": "S", "со": "S", "м": "S", "ж": "S", "жо": "S", "мо": "S", "мо-жо": "S", "с": "S", "п": "A",
         "числ.-п": "A", "мс-п": "A", "нсв": "V", "св": "V", "св-нсв": "V", "предл.": "PR", "союз": "CONJ",
         "н": "ADV", "вводн.": "ADV", "част.": "ADV", "межд.": "ADV", "предик.": "NI", "числ.": "NI", "мест.": "NI",
         "VERB": "V", "UNKN": "NI", "PREP": "PR", "ADJS": "A", "ADJF": "A", "NOUN": "S", "NPRO": "NI",
         "PRCL": "ADV", "ADVB": "ADV", "CONJ": "CONJ", "INFN": "V", "GRND": "V", "PRTS": "V", "PRTF": "V",
         "COMP": "A", "INTJ": "ADV", "NUMR": "NI", "PRED": "NI", "Prnt": "ADV", "сравн.": "ADV"}
cnj = ["и", "а", "но", "да", "если", "что", "когда", "или"]
predl = ["за", "для", "в", "о", "к", "из", "от", "по", "под", "с", "об", "обо", "до", "над", "на", "ко", "к", "без",
         "из", "у"]
ni = ["я", "мы", "ты", "вы", "он", "она", "оно", "они", "себя", "мой", "наш", "твой", "свой", "кто", "что", "чей",
      "этот", "это", "тот", "сам", "весь"]
adv = ["не", "ни", "затем", "тогда", "итак", "наверно", "бы", "ли", "уже", "же", "только", "вот", "видимо"]
adjs = {"ый": "ый", "ого": "ый", "ому": "ый", "ом": "ый",
        "ая": "ый", "ой": "ый", "ую": "ый", "ое": "ый", "ые": "ый", "ых": "ый", "ым": "ый",
        "ыми": "ый", "ий": "ий", "его": "ий", "ему": "ий", "ем": "ий",
        "яя": "ий", "ей": "ий", "юю": "ий", "ее": "ий", "ие": "ий", "их": "ий", "им": "ий", "ими": "ий"}

def fix_word(word):
    return word.lower().replace("ё", "е")


def read_lemmas():
    root = ET.ElementTree(file="data/dict.opcorpora.xml").getroot()
    for lem in root.find('lemmata'):
        l = lem.find('l')
        dictionary[int(lem.get('id'))] = (fix_word(l.get('t')), l.find('g').get('v'))

    for link in root.find('links'):
        dictionary[int(link.get('to'))] = dictionary[int(link.get('from'))]

    for i in dictionary:
        post = posts[dictionary[i][1]]
        dictionary[i] = (dictionary[i][0], post)


def read_forms_odict():
    with open('data/odict.csv', encoding="cp1251") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            n = len(row)
            for i in range(n):
                if i == 1:
                    continue
                if row[i] == "":
                    continue
                if (row[0], row[1]) not in forms[row[i]]:
                    forms[row[i]].append((row[0], posts[row[1]]))


def read_forms():
    tree = ET.ElementTree(file="data/dict.opcorpora.xml")
    root = tree.getroot()
    for lem in root.find('lemmata'):
        id = int(lem.get('id'))
        for form in lem.findall('f'):
            forms[form.get('t')].append(dictionary[id])


def read_forms_conll():
    with open("data/RNCgoldInUD_Morpho.conll", encoding="utf-8") as inp:
        for row in inp:
            spl = row.split("\t")[1:4]
            if len(spl) <= 3:
                continue
            if (spl[1], spl[2]) not in forms[spl[0]]:
                forms[spl[0]].append((row[1], row[2]))


def read_corpus_openc():
    tree = ET.ElementTree(file="data/annot.opcorpora.no_ambig_strict.xml")
    root = tree.getroot()
    for text in root.findall('text'):
        for paragraph in text.find('paragraphs').findall('paragraph'):
            for sentence in paragraph.findall('sentence'):
                for token in sentence.find('tokens').findall('token'):
                    l = token.find('tfr').find('v').find('l')
                    post = l.find('g').attrib['v']
                    if post == "PNCT":
                        continue
                    if dictionary.get(int(l.attrib['id'])) is None:
                        continue
                    freqs[dictionary[int(l.attrib['id'])]] += 1


def read_corpus_conll():
    with open("data/RNCgoldInUD_Morpho.conll", encoding="utf-8") as inp:
        for row in inp:
            spl = row.split("\t")[1:4]
            if len(spl) <= 3:
                continue
            if spl[2] in pst:
                freqs[(fix_word(spl[1]), spl[2])] += 1
            else:
                freqs[(fix_word(spl[1]), posts[spl[2]])] += 1


def resolve(word):
    lemmas = forms[word]
    if len(lemmas) == 1:
        return lemmas[0]

    ml, mp, mf = "", "", -1
    for lemma in lemmas:
        if freqs[lemma] is None:
            continue
        if mf < freqs[lemma]:
            ml, mp, mf = lemma[0], lemma[1], freqs[lemma]

    if mf == -1:
        lemma = random.choice(lemmas)
        return lemma
    else:
        return ml, mp


def adj(word):
    return len(word) > 3 and (word[-2:] in adjs or word[-3:] in adjs)


def to_lem(word):
    if len(word) >= 2 and word[-2:] in adjs:
        word = word[:-2] + adjs[word[-2:]]
    elif len(word) >= 3 and word[-3:] in adjs:
        word = word[:-3] + adjs[word[-3:]]
    return word


def run():
    file = open('in.txt', "r")
    out = open("out.txt", "w")
    for line in file:
        line = line.replace(",", "").strip()
        words = line.split(" ")
        res = ""
        flag = True  # first word
        for word in words:
            cword = word

            word = word.replace(".", "").replace("?", "").replace("!", "").strip()

            res += word + "{"

            word = word.lower().replace("ё", "е").strip()

            if cnj.__contains__(word):
                res += word + "=CONJ} "
            elif predl.__contains__(word):
                res += word + "=PR} "
            elif adv.__contains__(word):
                res += word + "=ADV} "
            elif forms.get(word) is None:
                res += word + "=NI} "
            else:
                lemma, post = resolve(word)

                if cword[0].isupper() and not flag and post == "S":
                    lemma = lemma[0].upper() + lemma[1:]

                if len(word) > 2 and post == "NI" and (
                        word.endswith("ть") or word.endswith("ться") or word.endswith("тся")):
                    lemma, post = word, "V"

                if post == "NI" and (
                        lemma.endswith("ой") or lemma.endswith("ое") or lemma.endswith("ый") or lemma.endswith("ая") or lemma.endswith("ые") or lemma.endswith("ий") or lemma.endswith("ей") or lemma.endswith("ому") or lemma.endswith("ему")):
                    post = "A"

                if len(word) > 2 and (
                        (word.endswith("о") and not word.endswith("ое")) or word.endswith("а") or word.endswith("я") or word.endswith("у") or word.endswith("ю") or word.endswith("и")) and post == "A":
                    lemma, post = word, "ADV"

                if post == "V":
                    if word.endswith("ся") or word.endswith("сь"):
                        if not lemma.endswith("ся"):
                            lemma += "ся"

                if post == "NI":
                    if adj(word):
                        res += to_lem(word) + "=A} "
                    else:
                        lemma, post = word, "ADV"

                res += lemma + "=" + post + "} "
            flag = False
        out.write(res + "\n")
    file.close()
    out.close()


if __name__ == "__main__":
    read_lemmas()
    read_forms()
    read_forms_odict()
    read_corpus_openc()
    read_corpus_conll()
    run()
