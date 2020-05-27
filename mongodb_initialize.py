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
import argparse

pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 30)

#############################################
### Parameters

# base_dir = os.path.realpath(os.path.dirname(__file__))
#
# with open(os.path.join(base_dir, 'parameters-dev.yml')) as param:
#     param = yaml.safe_load(param)

parser = argparse.ArgumentParser()
parser.add_argument('yaml_path')
args = parser.parse_args()

with open(args.yaml_path) as param:
    param = yaml.safe_load(param)

schema_dir = 'schemas'
cv_dir = 'CVs'

loc_yml = 'location_schema.yml'
loc_coll = 'location'

# loc_index1 = [('ref', 1)]
loc_index2 = [('geometry', '2dsphere')]

# license_yml = 'license_schema.yml'
# license_coll = 'license'
#
# license_index1 = [('operator', 1), ('dataset_id', 1)]

dataset_yml = 'dataset_schema.yml'
dataset_coll = 'dataset'

dataset_index1 = [('feature', 1), ('parameter', 1), ('method', 1), ('processing_code', 1), ('owner', 1), ('aggregation_statistic', 1), ('frequency_interval', 1)]

loc_dataset_yml = 'loc_dataset_gen_schema.yml'
loc_dataset_coll = 'loc_dataset_gen'

loc_dataset_index1 = [('location_id', 1), ('feature', 1), ('parameter', 1), ('method', 1), ('processing_code', 1), ('owner', 1), ('aggregation_statistic', 1), ('frequency_interval', 1)]

ts1_yml = 'result1_schema.yml'
ts1_coll = 'time_series_result'

ts1_index1 = [('location_id', 1), ('dataset_id', 1), ('from_date', 1)]

############################################
### Initialize the collections, set the schemas, and set the indexes

client = MongoClient(param['host'], password=param['root_password'], username=param['root_username'])

db = client[param['database']]

print(db.list_collection_names())

## location collection

with open(os.path.join(base_dir, schema_dir, loc_yml)) as yml:
    loc1 = yaml.safe_load(yml)

db.create_collection(loc_coll, validator={'$jsonSchema': loc1})

# db[loc_coll].create_index(loc_index1)
db[loc_coll].create_index(loc_index2)

## license collection

# with open(os.path.join(base_dir, schema_dir, license_yml)) as yml:
#     license1 = yaml.safe_load(yml)
#
# db.create_collection(license_coll, validator={'$jsonSchema': license1})
#
# db[license_coll].create_index(license_index1, unique=True)

## loc-dataset collection

with open(os.path.join(base_dir, schema_dir, loc_dataset_yml)) as yml:
    loc_dataset1 = yaml.safe_load(yml)

db.create_collection(loc_dataset_coll, validator={'$jsonSchema': loc_dataset1})

db[loc_dataset_coll].create_index(loc_dataset_index1, unique=True)

## dataset collection

with open(os.path.join(base_dir, schema_dir, dataset_yml)) as yml:
    dataset1 = yaml.safe_load(yml)

db.create_collection(dataset_coll, validator={'$jsonSchema': dataset1})

db[dataset_coll].create_index(dataset_index1, unique=True)

## time series result collection

with open(os.path.join(base_dir, schema_dir, ts1_yml)) as yml:
    ts1 = yaml.safe_load(yml)

db.create_collection(ts1_coll, validator={'$jsonSchema': ts1})

db[ts1_coll].create_index(ts1_index1, unique=True)


#########################################
### Reference collections

cv_list = os.listdir(os.path.join(base_dir, cv_dir))

for cv in cv_list:
    cv1 = pd.read_table(os.path.join(base_dir, cv_dir, cv))
    cv1 = cv1.drop_duplicates('name')
    cv1
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

for u in param['db_new_users']:
    try:
        db.command("createUser", u['user'], pwd=u['pwd'], roles=[u['role']])
    except:
        print('user already created...trying to update user...')
        try:
            db.command("updateUser", u['user'], roles=[u['role']])
        except:
            raise ValueError('Could not update user')

for u in param['admin_new_users']:
    try:
        client['admin'].command("createUser", u['user'], pwd=u['pwd'], roles=[u['role']])
    except:
        print('user already created...trying to update user...')
        try:
            client['admin'].command("updateUser", u['user'], roles=[u['role']])
        except:
            raise ValueError('Could not update user')

client.close()

## Remove original root user
client = MongoClient(param['host'], password=u['pwd'], username=u['user'])
client['admin'].command("dropUser", 'root')

client.close()
