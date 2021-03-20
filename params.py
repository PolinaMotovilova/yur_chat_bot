import re
import collections
from deeppavlov import configs, build_model
import json
from natasha import AddressExtractor

#deeppavlov(ner)
ner_model = build_model(configs.ner.ner_ontonotes_bert_mult, download=False)

# предобработка текста: удаление знаков препинания и лишних непечатных символов, приведение букв к нижнему регистру и лемматизация
def preprocessing(text):
    # очистить строку от символов переноса (заменить на пробелы) и убрать лишние пробелы и пустые строки
    text_prep = re.sub("^\s+|\n|\r|\s+$", '', text).lower()

    text_prep = re.sub(r'[^\w\s]','', text_prep)
    return text_prep

#deeppavlov(slotfill)
def slotfill(text):
    PIPELINE_CONFIG_PATH = configs.ner.slotfill_dstc2_raw
    slotfill_model = build_model(PIPELINE_CONFIG_PATH, download=False)
    return slotfill_model([preprocessing(text)])

# Regular expressions (поиск номера телефона)
def telephone_number(text):
    result = re.findall(r'(?:\+7|8)?(?:\-|\s)\(?\d{3,4}\)?\W\d{2,3}\W\d{2,3}\W\d{2,3}|\(\d{3,4}\)\W\d{2,3}\W\d{2,3}\W\d{2,3}',text)
    return result

#Natasha (поиск адреса)
extractor = AddressExtractor()
def address_extractor(text):
    matches = extractor(text)
    spans = [_.span for _ in matches]
    facts = [_.fact.as_json for _ in matches]
    return facts

#функция для поиска параметров в тексте, отправленном пользователем
def process_param(text, processing_type):
    params = {}
    if processing_type == 'dp ner':
        param = ['PERSON', 'ORG']
        ner_text = ner_model([text])
        result = []
        for i in range(len(ner_text[0][0])):
            for p in param:
                res = []
                if 'I-' + p in ner_text[1][0][i]:
                    result[-1][0] += ' ' + ner_text[0][0][i]
                elif p in ner_text[1][0][i]:
                    res.append(ner_text[0][0][i])
                    res.append(p)
                    result.append(res)
        if len(result) != 0:
            return result[0][0]
    if processing_type == 'dp slotfill':
        with open(r'C:\Users\xxmotovp\.deeppavlov\downloads\dstc2\dstc_slot_vals.json', encoding='UTF-8') as f:
            data = json.load(f)
        slot = slotfill(text)
        if len(slot[0]) != 0:
            return data[list(slot[0].keys())[0]][list(slot[0].values())[0]][0]
    if processing_type == 'reg exp':
        if len(telephone_number(text)) != 0:
            return ' '.join(telephone_number(text))
    if processing_type == 'natasha':
        natasha_text = address_extractor(text)
        address = ''
        for i in range(0, len(natasha_text)):
            for key, value in natasha_text[i].items():
                for j in range(0, len(value)):
                    for k, val in collections.OrderedDict(reversed(list(value[j].items()))).items():
                        address += val + ' '
        if len(address) != 0:
            return address