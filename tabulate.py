import os
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input-directory', '-i', default = 'jotxt')
parser.add_argument('--output-path', '-o', default = 'natu.txt')
parser.add_argument('--legifrance', default = 'https://www.legifrance.gouv.fr/jorf/jo/{year}/{month}/{day}/{num}')
parser.add_argument('--section', default = 'naturalisation')

args = parser.parse_args()

records = ['\t'.join(['section', 'date', 'url', 'decree', 'firstname', 'lastname', 'gender', 'birthdate', 'birthplace', 'dep', 'comment'])]

ignored = []

for f in os.listdir(args.input_directory):
    yearmonthday, num = f.split('_')[1:3]
    year, month, day = yearmonthday[:4], yearmonthday[4:6], yearmonthday[6:]
    date = day + '/' + month + '/' + year
    url = args.legifrance.format(year = year, month = month, day = day, num = num)

    lines = list(open(os.path.join(args.input_directory, f)))
    section = None
    record = None
    
    lines = list(filter(bool, map(str.strip, lines)))
    for i in range(len(lines)):
        L = lines[i]
        L = L.replace('  ', ' ')
        F = (re.split('[^a-zA-Z]', L) + [''])[0]
        l = L.lower()
        if 'sont naturalisés français' in l or 'l’acquisition de la nationalité française' in l:
            section = 'naturalisation'
            record = ''

        elif 'demandes de changement de nom' in l:
            section = 'changementdenom'
            record = ''

        elif 'Art.' in L:
            section = None
            record = ''

        elif 'libéré de l’allégeance française' in L:
            continue

        else:
            if args.section != section:
                ignored.append(L)

            if section == 'naturalisation':
                if L.endswith('.') and (record or F.isupper()):
                    record += L
                    if L.endswith('dép.') or L.endswith('Dt.') or record.count('(') != record.count(')'):
                        continue

                    if not 'né' in record.lower():
                        record = ''
                        continue

                    name = record.split(')')[0]
                    lastname, firstname = name.split('(')[0].strip(), name.split('(')[1].rstrip(')')
                    gender = 'm' if 'né le' in record.lower() else 'f'
                    birth = re.split('NAT|EFF|LIB', record.split('é le' if gender == 'm' else 'ée le')[1].strip())[0]
                    birthdate = birth.split()[0]
                    birthplace = ' '.join(birth.split()[1:]).strip('àu ,')
                    dep = record.split('dép.')[1].split(',')[0].strip() if 'dép' in record.lower() else ''
                    comment = ''

                    if args.section == section:
                        records.append('\t'.join([section, date, url, f.rstrip('.txt'), firstname, lastname, gender, birthdate, birthplace, dep, comment.replace('\t', '')]))
                    record = ''
                
                elif F.isupper() and not record and 'né' in l:
                    record = L
                
                elif record:
                    record += L

                else:
                    ignored.append(L)
                    
            if section == 'changementdenom':
                if L.endswith('.'):
                    record += L
                    if args.section == section:
                        firstname = lastname = gender = birthdate = birthplace = dep = ''
                        comment = record
                        records.append('\t'.join([section, date, url, f.rstrip('.txt'), firstname, lastname, gender, birthdate, birthplace, dep, comment.replace('\t', '')]))
                    record = ''
                
                elif not L.startswith('No. ') and not L.startswith('No '):
                    record += L

open(args.output_path, 'w').write('\n'.join(records))
open(args.output_path + '.ignored.txt', 'w').write('\n'.join(ignored))
