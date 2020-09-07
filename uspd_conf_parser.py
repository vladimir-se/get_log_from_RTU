#!/usr/bin/env python3
#coding: utf-8

import sys
import os
import re
import xlsxwriter

values = {"f":"Частота (мгновенная)",
    "Icp":"Ток (мгновенный)",
    "Ia":"Ток (мгновенный):фаза А",
    "Ib":"Ток (мгновенный):фаза В",
    "Ic":"Ток (мгновенный):фаза С",
    "Ua":"Напряжение (мгновенное):фаза А",
    "Ub":"Напряжение (мгновенное):фаза В",
    "Uc":"Напряжение (мгновенное):фаза С",
    "Pcym":"Активная мощность+ (мгновенная)",
    "Pa":"Активная мощность+ (мгновенная):фаза А",
    "Pb":"Активная мощность+ (мгновенная):фаза В",
    "Pc":"Активная мощность+ (мгновенная):фаза С",
    "Q":"Реактивная мощность+ (мгновенная)",
    "Qa":"Реактивная мощность+ (мгновенная):фаза А",
    "Qb":"Реактивная мощность+ (мгновенная):фаза В",
    "Qc":"Реактивная мощность+ (мгновенная):фаза С",
    "S":"Полная мощность+ (мгновенная)",
    "Sa":"Полная мощность+ (мгновенная):фаза А",
    "Sb":"Полная мощность+ (мгновенная):фаза В",
    "Sc":"Полная мощность+ (мгновенная):фаза С",
    "Текущее состояние дискретного входа":"Текущее состояние дискретного входа",
    "Значение аналоговой величины (мгновенное)":"Значение аналоговой величины (мгновенное)",
    "Признак диагностического сообщения: контроль рабочего режима УСПД":"Признак диагностического сообщения: контроль рабочего режима УСПД"}

discrete = {}
diagnostics = {}
analog = {}
counter = {}

all_signals = 0
discrete_signals = 0
analog_signals = 0
count_in_counter_signals = 0
counter_signals = 0

try:
    fil = sys.argv[1]
except:
    # fil = os.path.dirname(__file__)+os.sep+"ges-15_101_1.txt"
    print(os.path.basename(__file__) + " файл конфигурации")
    sys.exit(1)

with open(fil, 'r', encoding='utf-8') as f:
    tmp = None
    for line in f:
        line = line.encode('utf-8').decode('utf-8')
        # получение строки
        s = re.findall('^.\d+\s+.\d+\s+.\s\+\s{1,2}.\w+[\w\s.]+[:][\w\d\s\-,<>\*\"\'.()]+\s*.[\w\d\s\+-,.():]+', line)

        # обработка строки
        if len(s) > 0:
            s = re.split('\s{2,}[│]', s[0])
            # замена названий инженерными велечинами 
            for key, value in values.items():
                if s[4].strip() == value:
                    s[4] = key
            # удаление возможной лишней нумерации и разделение 3го поля на типа и наименование
            s3_tmp = [x.strip() for x in s[3].split(':')]
            s3_tmp[1] = re.sub(r'^[(]\s*\d*[)]\s*', '', s3_tmp[1])
            s[3] = s3_tmp
            # формирование списка ТИ по присоединениям
            if s[3][0] == 'Счетчик': # обработка параметров счетчиков(ТИ)
                if tmp == None or tmp != s[3][1]:
                    tmp = s[3][1]
                    counter[tmp] = {}
                    counter[tmp].update({s[4]:s[1]})
                elif tmp == s[3][1]:
                    counter[tmp].update({s[4]:s[1]})
            elif s[3][0] == 'Дискр.вход': # ТС
                discrete[s[3][1]] = s[1]
            elif s[3][0] == 'Аналог.вход': # ТИ
                analog[s[3][1]] = s[1]
            elif s[3][0] == 'УСПД': # диагностика 
                diagnostics[s[3][1]] = s[1]

workbook = xlsxwriter.Workbook(os.path.dirname(__file__)+os.sep+fil[:-3]+'xlsx')
worksheet = workbook.add_worksheet()

cell_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_name': 'Times New Roman',
        'font_size': 10
    })

line = 1
width_name = 0
width_addr = 0

worksheet.merge_range('A{0}:C{1}'.format(1, 1), 'Список телеизмерений', cell_format)
worksheet.set_row(1, 50)
worksheet.write('A{0}'.format(2), 'Присоединение', cell_format)
worksheet.write('B{0}'.format(2), 'Передаваемая\n информация', cell_format)
worksheet.write('C{0}'.format(2), 'Адрес\n информационных\n объектов', cell_format)
line += 2
for name, param in counter.items():
    start_line = line
    if width_name < len(name): width_name = len(name)
    for transmit_value, addr in param.items():
        worksheet.write('B{0}'.format(line), transmit_value, cell_format)
        worksheet.write('C{0}'.format(line), addr, cell_format)
        all_signals += 1 # общее число сигналов
        analog_signals += 1 # общее количество ТИ
        line += 1
    worksheet.merge_range('A{0}:A{1}'.format(start_line, line-1), name, cell_format)
    worksheet.set_column('A:A', width_name)
    counter_signals += 1 # количество точек измерения 
#
for name, addr in analog.items():
    worksheet.write('A{0}'.format(line), name, cell_format)
    worksheet.write('B{0}'.format(line), addr, cell_format)
    all_signals += 1 # общее число сигналов
    analog_signals += 1 # общее количество ТИ
    line += 1

header = ['Список телесигналов', 'Список диагностических сигналов']
for i in [0, discrete, 1, diagnostics]:
    if type(i) == int:
        line += 2
        worksheet.merge_range('A{0}:B{1}'.format(line, line), header[i], cell_format)
        worksheet.set_row(line, 50)
        worksheet.write('A{0}'.format(line+1), 'Присоединение', cell_format)
        worksheet.write('B{0}'.format(line+1), 'Адрес\n информационных\n объектов', cell_format)
        line += 2
    else:
        for name, addr in i.items():
            if width_name < len(name): width_name = len(name)
            worksheet.write('A{0}'.format(line), name, cell_format)
            worksheet.set_column('A:A', width_name)
            worksheet.write('B{0}'.format(line), addr, cell_format)
            all_signals += 1 # общее число сигналов
            discrete_signals += 1 # общее количество дискретных сигналов
            line += 1
workbook.close()

print("Общее количество сигналов: {0}".format(all_signals))
print("Общее количество дискретных сигналов: {0}".format(discrete_signals))
print("Общее количество аналоговых сигналов: {0}".format(analog_signals))
print("Общее количество точек замера: {0}".format(counter_signals))