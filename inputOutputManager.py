#!/usr/bin/env python
'''
COPYRIGHT:
Python-tesseract is released under the GPL v3.
Copyright (c) Samuel Hoffstaetter, 2009
http://wiki.github.com/hoffstaetter/python-tesseract

'''
tesseract_cmd = 'tesseract'

import Image
import StringIO
import subprocess
import sys
import os
import enchant
import getkeyword
import dropbox
import threading
from gistapi import Gist, Gists
from pastebin_python import PastebinPython
from pastebin_python.pastebin_exceptions import PastebinBadRequestException, PastebinNoPastesException, PastebinFileException
from pastebin_python.pastebin_constants import PASTE_PUBLIC, EXPIRE_10_MIN
from pastebin_python.pastebin_formats import FORMAT_NONE, FORMAT_PYTHON, FORMAT_HTML

__all__ = ['image_to_string']

def dropbox_put():
    app_key = 'g031xqq01hzxiqa'
    app_secret = '0p5jkff6dijruh8'
    flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
    authorize_url = flow.start()
    print '1. Go to: ' + authorize_url
    print '2. Click "Allow" (you might have to log in first)'
    print '3. Copy the authorization code.'
    code = raw_input("Enter the authorization code here: ").strip()
    access_token, user_id = flow.finish(code)
    client = dropbox.client.DropboxClient(access_token)
    f = open('working-draft.txt')
    response = client.put_file('/magnum-opus.txt', f)

def dropbox_get(filename):
    app_key = 'g031xqq01hzxiqa'
    app_secret = '0p5jkff6dijruh8'
    flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
    authorize_url = flow.start()
    print '1. Go to: ' + authorize_url
    print '2. Click "Allow" (you might have to log in first)'
    print '3. Copy the authorization code.'
    code = raw_input("Enter the authorization code here: ").strip()
    access_token, user_id = flow.finish(code)
    client = dropbox.client.DropboxClient(access_token)
    try:
        f, metadata = client.get_file_and_metadata(filename)
        image_to_string(f)
        f.close()
    except:
        pass

def run_tesseract(input_filename, output_filename_base, lang=None, boxes=False):
    command = [tesseract_cmd, input_filename, output_filename_base]

    if lang is not None:
        command += ['-l', lang]

    if boxes:
        command += ['batch.nochop', 'makebox']

    proc = subprocess.Popen(command,
            stderr=subprocess.PIPE)
    return (proc.wait(), proc.stderr.read())

def cleanup(filename):
    try:
        os.remove(filename)
    except OSError:
        pass

def get_errors(error_string):
    lines = error_string.splitlines()
    error_lines = tuple(line for line in lines if line.find('Error') >= 0)
    if len(error_lines) > 0:
        return '\n'.join(error_lines)
    else:
        return error_string.strip()

def tempnam():
    stderr = sys.stderr
    try:
        sys.stderr = StringIO.StringIO()
        return os.tempnam(None, 'tess_')
    finally:
        sys.stderr = stderr

class TesseractError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        self.args = (status, message)

def getDictionaryWords(wordlist):
    d = enchant.Dict("en_US")
    words = wordlist.split()
    dictwords = []

    for word in words:
        if d.check(word):
            dictwords.append(word)

    inputstring = ""
    for word in words:
        inputstring+=str(word)+" "

    returnwordstospeak = getkeyword.fetchkeywords(inputstring)

    returnstring=""
    for word in returnwordstospeak:
        returnstring+= word+" "

    return returnstring

def worker():
    dropbox_get('test1.jpeg')
    threading.Timer(1,worker).start ()

def image_to_string(image, lang=None, boxes=False):
    input_file_name = '%s.bmp' % tempnam()
    output_file_name_base = tempnam()
    if not boxes:
        output_file_name = '%s.txt' % output_file_name_base
    else:
        output_file_name = '%s.box' % output_file_name_base
    try:
        image.save(input_file_name)
        status, error_string = run_tesseract(input_file_name,
                                             output_file_name_base,
                                             lang=lang,
                                             boxes=boxes)
        if status:
            errors = get_errors(error_string)
            raise TesseractError(status, errors)
        f = file(output_file_name)
        try:
            return f.read().strip()
        finally:
            f.close()
    finally:
        cleanup(input_file_name)
        cleanup(output_file_name)

if __name__ == '__main__':
        worker()
        if len(sys.argv) == 2:
            filename = 'test1.jpeg'
            try:
                image = Image.open(filename)
            except IOError:
                sys.stderr.write('ERROR: Could not open file "%s"\n' % filename)
                exit(1)
            returnString = image_to_string(image)
            finalresult =  getDictionaryWords(returnString)
            print getDictionaryWords(returnString)
            pbin = PastebinPython(api_dev_key='3e732a377fe2a5dd72c73afd1bed2949')
            try:
                pbin.createAPIUserKey('hackmit','hackmit')
                print pbin.createPaste(finalresult, 'Looking glass...', FORMAT_HTML, PASTE_PUBLIC, EXPIRE_10_MIN)
            except PastebinBadRequestException as e:
                print e.message
            except PastebinFileException as e:
                print e.message
        elif len(sys.argv) == 4 and sys.argv[1] == '-l':
            lang = sys.argv[2]
            filename = sys.argv[3]
            try:
                image = Image.open(filename)
            except IOError:
                sys.stderr.write('ERROR: Could not open file "%s"\n' % filename)
                exit(1)

            returnString = image_to_string(image, lang=lang)
            finalresult = getDictionaryWords(returnString)
            print getDictionaryWords(returnString)
        else:
            sys.stderr.write('Usage: python tesseract.py [-l language] input_file\n')
            exit(2)