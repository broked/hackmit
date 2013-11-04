#!/usr/bin/env python
from __future__ import print_function
from alchemyapi import AlchemyAPI
import json

def fetchkeywords(demo_text):
    alchemyapi = AlchemyAPI()
    response = alchemyapi.keywords('text',demo_text, { 'sentiment':1 })
    listoftopwords = []

    if response['status'] == 'OK':
        for keyword in response['keywords']:
	        listoftopwords.append(keyword['text'])

    return listoftopwords
