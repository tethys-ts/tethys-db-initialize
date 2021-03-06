# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 08:04:46 2019

@author: michaelek
"""
import os
import pandas as pd
import pymongo
from pymongo import MongoClient
import yaml
import json
from time import sleep

pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 30)

#############################################
### Parameters

base_dir = os.path.realpath(os.path.dirname(__file__))

try:
    param = os.environ.copy()
    database = param['DATABASE']
    root_user = param['MONGO_INITDB_ROOT_USERNAME']
    root_pass = param['MONGO_INITDB_ROOT_PASSWORD']
except:
    with open(os.path.join(base_dir, 'parameters.yml')) as param:
        param = yaml.safe_load(param)

    database = param['DATABASE']
    root_user = param['MONGO_INITDB_ROOT_USERNAME']
    root_pass = param['MONGO_INITDB_ROOT_PASSWORD']

schema_dir = 'schemas'
cv_dir = 'CVs'

loc_yml = 'sampling_site_schema.yml'
loc_coll = 'sampling_site'

loc_index1 = [('ref', 1)]
loc_index2 = [('geometry', '2dsphere')]

# license_yml = 'license_schema.yml'
# license_coll = 'license'
#
# license_index1 = [('operator', 1), ('dataset_id', 1)]

log_yml = 'processing_log_schema.yml'
log_coll = 'processing_log'

log_index1 = [('date', 1), ('dataset_id', 1)]

dataset_yml = 'dataset_schema.yml'
dataset_coll = 'dataset'

dataset_index1 = [('feature', 1), ('parameter', 1), ('method', 1), ('processing_code', 1), ('owner', 1), ('aggregation_statistic', 1), ('frequency_interval', 1), ('utc_offset', 1)]

loc_dataset_yml = 'site_dataset_schema.yml'
loc_dataset_coll = 'site_dataset'

loc_dataset_index1 = [('site_id', 1), ('dataset_id', 1)]

ts1_yml = 'result1_schema.yml'
ts1_coll = 'time_series_result'

ts1_index1 = [('dataset_id', 1), ('site_id', 1), ('from_date', 1)]

ts2_yml = 'result_simulation_schema.yml'
ts2_coll = 'time_series_simulation'

ts2_index1 = [('dataset_id', 1), ('site_id', 1), ('simulation_date', 1)]

sleep(3)

############################################
### Initialize the collections, set the schemas, and set the indexes

client = MongoClient('db', password=root_pass, username=root_user)
# client = MongoClient('127.0.0.1', password=root_pass, username=root_user)
# client = MongoClient('tethys-ts.duckdns.org', password=root_pass, username=root_user)

db = client[database]

print(db.list_collection_names())

## location collection

with open(os.path.join(base_dir, schema_dir, loc_yml)) as yml:
    loc1 = yaml.safe_load(yml)

try:
    db.create_collection(loc_coll, validator={'$jsonSchema': loc1})
except:
    db.command('collMod', loc_coll, validator= {'$jsonSchema': loc1})
    db[loc_coll].drop_indexes()

db[loc_coll].create_index(loc_index1)
db[loc_coll].create_index(loc_index2)


## license collection

# with open(os.path.join(base_dir, schema_dir, license_yml)) as yml:
#     license1 = yaml.safe_load(yml)
#
# db.create_collection(license_coll, validator={'$jsonSchema': license1})
#
# db[license_coll].create_index(license_index1, unique=True)

## log collection

with open(os.path.join(base_dir, schema_dir, log_yml)) as yml:
    log1 = yaml.safe_load(yml)

try:
    db.create_collection(log_coll, validator={'$jsonSchema': log1})
except:
    db.command('collMod', log_coll, validator= {'$jsonSchema': log1})
    db[log_coll].drop_indexes()

db[log_coll].create_index(log_index1)

## loc-dataset collection

with open(os.path.join(base_dir, schema_dir, loc_dataset_yml)) as yml:
    loc_dataset1 = yaml.safe_load(yml)

try:
    db.create_collection(loc_dataset_coll, validator={'$jsonSchema': loc_dataset1})
except:
    db.command('collMod', loc_dataset_coll, validator= {'$jsonSchema': loc_dataset1})
    db[loc_dataset_coll].drop_indexes()

db[loc_dataset_coll].create_index(loc_dataset_index1, unique=True)

## dataset collection

with open(os.path.join(base_dir, schema_dir, dataset_yml)) as yml:
    dataset1 = yaml.safe_load(yml)

try:
    db.create_collection(dataset_coll, validator={'$jsonSchema': dataset1})
except:
    db.command('collMod', dataset_coll, validator= {'$jsonSchema': dataset1})
    db[dataset_coll].drop_indexes()

db[dataset_coll].create_index(dataset_index1, unique=True)

## time series result collection

with open(os.path.join(base_dir, schema_dir, ts1_yml)) as yml:
    ts1 = yaml.safe_load(yml)

try:
    db.create_collection(ts1_coll, validator={'$jsonSchema': ts1})
except:
    db.command('collMod', ts1_coll, validator= {'$jsonSchema': ts1})
    db[ts1_coll].drop_indexes()

db[ts1_coll].create_index(ts1_index1, unique=True)

## time series simulation collection

with open(os.path.join(base_dir, schema_dir, ts2_yml)) as yml:
    ts2 = yaml.safe_load(yml)

try:
    db.create_collection(ts2_coll, validator={'$jsonSchema': ts2})
except:
    db.command('collMod', ts2_coll, validator= {'$jsonSchema': ts2})
    db[ts2_coll].drop_indexes()

db[ts2_coll].create_index(ts2_index1, unique=True)

#########################################
### Reference collections

cv_list = os.listdir(os.path.join(base_dir, cv_dir))

for cv in cv_list:
    cv1 = pd.read_table(os.path.join(base_dir, cv_dir, cv))
    cv1 = cv1.drop_duplicates('name')
    cv2 = cv1.to_dict('records')
    name = cv.split('.')[0]
    try:
        db.create_collection(name)
    except:
        db.drop_collection(name)
        db.create_collection(name)
    db[name].create_index('name', unique=True)
    db[name].insert_many(cv2)

print(db.list_collection_names())

#########################################
### Create additional users

if ('READER_USERNAME' in param) and ('READER_PASSWORD' in param):
    user = param['READER_USERNAME']
    password = param['READER_PASSWORD']
    try:
        db.command("createUser", user, pwd=password, roles=['read'])
    except:
        print('user already created...trying to update user...')
        try:
            db.command("updateUser", user, roles=['read'])
        except:
            raise ValueError('Could not update user')

if ('RW_USERNAME' in param) and ('RW_PASSWORD' in param):
    user = param['RW_USERNAME']
    password = param['RW_PASSWORD']
    try:
        db.command("createUser", user, pwd=password, roles=['readWrite'])
    except:
        print('user already created...trying to update user...')
        try:
            db.command("updateUser", user, roles=['readWrite'])
        except:
            raise ValueError('Could not update user')

client.close()
