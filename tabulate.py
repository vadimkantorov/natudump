import os
import re
import argparse

digits = lambda s: ''.join(c for c in s if c.isdigit())

def extract_record(record, year, section, date, url, basename):
    comment = ''
    genderstr, gender = None, None
    for k, v in {'née le' : 'f', 'né le' : 'm', ', née' : 'f','néele' : 'f',  'néle' : 'm', ', né' : 'm'}.items():
        if k in record.lower():
            gender, genderstr = v, k
            break

    if genderstr is None:
        firstname = record.split('(')[0]
        lastname = action = gender = birthdate = birthplace = birthcountry = dep = ''
        comment = record

    else:
        gendersplitted = record.split(genderstr) or record.lower().split(genderstr)
        name = gendersplitted[0]
        lastname, firstname = name.split('(')[0], name.split('(')[-1]
        lastname, firstname = lastname.strip().strip('(),'), firstname.strip().strip('(),') 

        birth = re.split('NAT|EFF|LIB|REI', gendersplitted[-1].strip())[0]

        record_nospace = record.replace(' ', '').lower()
        action = 'NAT' if ',nat,' in record_nospace else 'EFF' if ',eff,' in record_nospace else 'LIB' if ',lib,' in record_nospace else 'REI' if ',rei,' in record_nospace else ''
        re_birthdate = r'[ \-/0-9]+'
        birthdate = (re.findall(re_birthdate, birth) + [''])[0].replace('-', '').replace('/', '').replace(' ', '')
        birthdate = (birthdate[:2] + '/' + birthdate[-6:-4] + '/' + birthdate[-4:]).strip('/')
        birthplace = ' '.join(re.split(re_birthdate, birth)).strip('àau,. ')

        if birthplace.count('(') == birthplace.count(')') == 1:
            birthcountry = birthplace.split('(')[1].split(')')[0].strip(' ,')
            birthplace = birthplace.split('(')[0].strip(' ,')
        else:
            birthcountry = ''
        dep = digits(record_nospace.split('dép')[-1].split(',')[0].strip()) if 'dép' in record.lower() else ''

    return (year, section, date, url, basename.rstrip('.txt'), action, lastname.capitalize(), firstname, gender, birthdate, birthplace, birthcountry, dep, comment.replace('\t', ''))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-directory', '-i', default = 'txtjo')
    parser.add_argument('--output-path', '-o', default = 'natufrance.tsv')
    parser.add_argument('--legifrance', default = 'https://www.legifrance.gouv.fr/jorf/jo/{year}/{month}/{day}/{num}')
    parser.add_argument('--section', default = 'naturalisation', help = 'nat : naturalisé français ; rei : réintégré dans la nationalité française ; eff : enfant saisi par l’effet collectif attaché à l’acquisition de la nationalité française par ses parents ; lib : libéré de l’allégeance française')
    args = parser.parse_args()


    records = []
    joe = {}

    for basename in os.listdir(args.input_directory): #['JORF_20150116_13.pdf.txt']:#
        yearmonthday, num = basename.split('_')[1:3]
        year, month, day = yearmonthday[:4], yearmonthday[4:6], yearmonthday[6:]
        date = day + '/' + month + '/' + year
        url = args.legifrance.format(year = year, month = month, day = day, num = num)

        lines = list(open(os.path.join(args.input_directory, basename)))
        section = None
        record = None
        
        lines = list(filter(bool, map(str.strip, lines)))
        ignore = True
        for i in range(len(lines)):
            L = lines[i]
            L = L.replace('  ', ' ').replace(':', '.').strip()
            dots = '-_;·~·•'
            for c in dots:
                if L and L[-1] == c:
                    L = L.rstrip(c) + '.'
            for c in dots:
                L = L.replace(c, ' ')
            L = L.strip()

            F = (re.split('[^a-zA-Z]', L) + [''])[0]
            l = L.lower()
            
            if section == args.section:
                ignore = False

            if 'sont naturalisés français' in l:# or 'l’acquisition de la nationalité française' in l:
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
                if section == 'naturalisation':
                    if (L.endswith('.') or (l.count('dép') >= 1 and L.count('Dt') >= 1)) and (bool(record) or F.isupper()):
                        record += L + ' '
                        if L.endswith('dép.') or L.endswith('Dt.'):# or record.count('(') != record.count(')'):
                            continue

                        if 'né' not in record.lower():
                            record = ''
                            continue

                        if section == args.section:
                            records.append(extract_record(record, year, section, date, url, basename))
                            if not records[-1]:
                                records.pop()

                        record = ''
                    
                    elif F.isupper() and not record and 'né' in l:
                        record = L
                    
                    elif record:
                        record += L
                        
                if section == 'changementdenom':
                    if L.endswith('.'):
                        record += L
                        if section == args.section:
                            firstname = lastname = gender = birthdate = birthplace = birthcountry = dep = action = ''
                            records.append((year, section, date, url, basename.rstrip('.txt'), action, lastname, firstname, gender, birthdate, birthplace, birthcountry, dep, record.replace('\t', '')))
                        record = ''
                    
                    elif not L.startswith('No. ') and not L.startswith('No '):
                        record += L
        joe[basename] = ignore

    open(args.output_path, 'w').write('\n'.join(map('\t'.join, [('year', 'section', 'date', 'url', 'decree', 'action', 'lastname', 'firstname', 'gender', 'birthdate', 'birthplace', 'birthcountry', 'dep', 'comment')] + sorted(records, key = lambda r: (r[6], r[7])))))
    open(args.output_path + '.joe.txt', 'w').write('\n'.join(k + '\t' + str(int(v)) for k, v in joe.items()))
