import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input-directory', '-i', default = 'jotxt')
parser.add_argument('--output-path', '-o', default = 'natu.txt')
parser.add_argument('--legifrance', default = 'https://www.legifrance.gouv.fr/jorf/jo/{year}/{month}/{day}/{num}')

args = parser.parse_args()

records = []
for f in os.listdir(args.input_directory):
    yearmonthday, num = f.split('_')[1:3]
    year, month, day = yearmonthday[:4], yearmonthday[4:6], yearmonthday[6:]
    url = args.legifrance.format(year = year, month = month, day = day, num = num)

    lines = list(open(os.path.join(args.input_directory, f)))
    section = None
    record = None
    
    for L in filter(bool, map(str.strip, lines)):
        F = L.split()[0]
        l = L.lower().replace('  ', ' ')
        if 'sont naturalisés français' in l or 'l’acquisition de la nationalité française' in l:
            section = 'naturalisation'
            record = ''

        elif 'demandes de changement de nom' in l:
            section = 'changementdenom'
            record = ''

        else:
            if section == 'naturalisation':
                if L.endswith('.') and not L[-2].isalpha():
                    record += L
                    records.append(':'.join([section, url, f.rstrip('.txt'), record]))
                    record = ''
                
                elif F.isalpha() and F.isupper():
                    record = L
                
                else:
                    record += L
                    
            if section == 'changementdenom':
                if L.endswith('.'):
                    record += L
                    records.append(':'.join([section, url, f.rstrip('.txt'), record]))
                    record = ''
                
                elif not L.startswith('No. '):
                    record += L

open(args.output_path, 'w').write('\n'.join(records))
