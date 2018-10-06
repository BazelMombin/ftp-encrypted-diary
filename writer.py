import os
import sys
import struct
import hashlib
import argparse
import getpass
import configparser
import csv
import datetime


from ftplib import FTP_TLS
import ssl
from Crypto import Random
from Crypto.Cipher import AES
from halo import Halo

AES_MODE = AES.MODE_CBC
IV_SIZE = AES.block_size
CHUNK_SIZE = 64 * 1024

def connect():
    config = configparser.ConfigParser()
    config.read('config.ini')
    ftp = FTP_TLS()
    ftp.ssl_version = ssl.PROTOCOL_SSLv23
    ftp.connect(config['node53']['address'], 21)
    ftp.login(config['node53']['user'], config['node53']['password'])
    print(ftp.prot_p())
    return ftp


def _generate_key_from_password(password):

    key = password.encode('utf-8')
    return hashlib.sha256(key).digest()


def encrypt_file(password, in_filename, out_filename=None, chunksize=CHUNK_SIZE):
    key = _generate_key_from_password(password)

    if not out_filename:
        out_filename = in_filename + '.enc'

    iv = Random.new().read(IV_SIZE)
    encryptor = AES.new(key, AES_MODE, iv)
    filesize = os.path.getsize(in_filename)

    with open(in_filename, 'rb') as infile:
        with open(out_filename, 'wb') as outfile:
            outfile.write(struct.pack('<Q', filesize))
            outfile.write(iv)

            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    chunk += b' ' * (16 - len(chunk) % 16)

                outfile.write(encryptor.encrypt(chunk))




### enrty creation + csv
fieldnames = ['date', 'entry']
entry = input('Create entry: \n')
obj1 = {'date': str(datetime.date.today()), 'entry': entry}

file = open('diary.csv', 'a', newline='')
writer = csv.DictWriter(file, fieldnames=fieldnames)
### writer.writeheader()
writer.writerow(obj1)
file.close()


spinner = Halo(text='Encrypting', spinner='dots')


### encryption

psswrd = input('Password: \n')

spinner.start()
encrypt_file(psswrd, 'diary.csv')

spinner.succeed('Encryption successful')
spinner = Halo(text='Uploading', spinner='dots')
spinner.start()


try:

    ### File upload
    ftp = connect()
    ftp.cwd('/home/Docs/backup/diary')
    file = open('diary.csv.enc','rb')                  
    r1 = ftp.storbinary('STOR diary.csv.enc', file)   
    file.close()    
    spinner.succeed('Upload successful')

except:
    spinner.warn('Failed to upload')



os.remove('diary.csv.enc')
#### end