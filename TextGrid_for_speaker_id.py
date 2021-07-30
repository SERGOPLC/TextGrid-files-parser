import os
import pandas as pd
import textgrid
import re
import matplotlib.pyplot as plt

path = 'C:/Users/Sergey/Desktop/test_id/'  # путь к TextGrid файлам. Пример: 'C:/Users/Sergey/Desktop/ben_mfa/'

filenames = os.listdir(path)  # собираем имена файлов

words = []
words_duration = []
words_path = []
words_phones = []
words_speaker_id = []
phones = []
phones_duration = []
phones_path = []
phones_speaker_id = []

# парсим файлы
for k in filenames:
    tg = textgrid.TextGrid.fromFile(path + k)  # читаем файл
    result = re.split(r'_', k)
    result = result[0]
    for i in tg[0]:  # идем по словам
        iv = pd.Interval(left=i.minTime, right=i.maxTime, closed='left')  # задаем временной интервал
        if i.mark != '':
            words.append(i.mark)
            words_duration.append(i.maxTime - i.minTime)
            words_path.append(k)
            words_speaker_id.append(result)
            tmp = []

            for j in tg[1]: # идем по словам идем по фонемам
                if j.minTime in iv:
                    phones.append(j.mark)
                    phones_duration.append(j.maxTime - j.minTime)
                    phones_path.append(k)
                    phones_speaker_id.append(result)
                    tmp.append(j.mark)

            if tmp:
                words_phones.append(tmp)

            tmp = []

# создаем датафреймы
df_words = pd.DataFrame(list(zip(words, words_phones, words_duration, words_path, words_speaker_id)),
                        columns=['words', 'phones', 'duration', 'path', 'speaker_id'])

df_phones = pd.DataFrame(list(zip(phones, phones_duration, phones_path, phones_speaker_id)),
                         columns=['phones', 'duration', 'path', 'speaker_id'])

speaker_uniq = df_words['speaker_id'].unique()
for id in speaker_uniq:

    # выбираем данные с опредленным спикером
    df_words_tmp = df_words[df_words['speaker_id'] == id]
    df_phones_tmp = df_phones[df_phones['speaker_id'] == id]

    # создаем датафреймы с уникальными значениями фонем и солов
    df_phones_uniq = df_phones_tmp['phones'].value_counts()
    df_phones_uniq = df_phones_uniq.to_frame().reset_index()
    df_phones_uniq = df_phones_uniq.rename(columns={'phones': 'count', 'index': 'phones'})

    df_words_uniq = df_words_tmp['words'].value_counts()
    df_words_uniq = df_words_uniq.to_frame().reset_index()
    df_words_uniq = df_words_uniq.rename(columns={'words': 'count', 'index': 'words'})

    # считаем среднеквадратичное по длительности слов
    df_words_uniq = df_words_uniq.sort_values('words')
    df_test = df_words_tmp.groupby('words').std()
    lst = df_test['duration'].to_list()
    df_words_uniq['std'] = lst
    df_words_uniq = df_words_uniq.sort_index()

    # находим отклонения от нормального распределения
    axes = df_words_uniq.boxplot(column=['std'], return_type='dict')

    value = 0
    for i in axes['whiskers']:
        for j in i._path.vertices:
            for k in j:
                if (k > value) and k != 1.0:
                    value = k


    df_words_uniq['need to change'] = False
    df_words_uniq.loc[df_words_uniq['std'] > value, 'need to change'] = True

    l_ntc = df_words_uniq[df_words_uniq['need to change'] == True]['words'].tolist()

    df_ntc = df_words_tmp[df_words_tmp['words'] == l_ntc[0]]

    for i in l_ntc[1:]:
        df_ntc = pd.concat([df_ntc, df_words_tmp[df_words_tmp['words'] == i]])

    df_ntc.to_csv(id + '_words.csv', index=False)

    # считаем среднеквадратичное по длительности фонем
    df_phones_uniq = df_phones_uniq.sort_values('phones')
    df_phones_test = df_phones_tmp.groupby('phones').std()
    phones_lst = df_phones_test['duration'].to_list()
    df_phones_uniq['std'] = phones_lst
    df_phones_uniq = df_phones_uniq.sort_index()

    # берем три самых долгих по продолжительности фонемы (если нужно больше - увеличитье tail())
    phones_l_ntc = df_phones_uniq.sort_values('std')['phones'].tail(3).tolist()

    # находим "ненормальные" слова с долгими фонемами
    df_phones_ntc = df_ntc[df_ntc.phones.astype(str).str.contains(phones_l_ntc[0])]

    for i in phones_l_ntc[1:]:
        df_phones_ntc = pd.concat([df_phones_ntc, df_ntc[df_ntc.phones.astype(str).str.contains(i)]])

    df_phones_ntc.to_csv(id + '_words_with_phones.csv', index=False)
