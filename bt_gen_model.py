
# General Imports
import json
import os
import glob
from pathlib import Path
from typing import List
import subprocess

# Parsing Imports
import msgspec
from genson import SchemaBuilder
import pandas as pd


# Flattens JSON into nested name for CSV output. WARNING: RECURSIVE
def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '.')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '.')
                i += 1
        else:
            out[name[:-1]] = x
    flatten(y)
    return out


# Parses JSONs matching a prefix and rejects those with a specific substring
def parseModels(path, prefix, reject, modelType):
    models: List[modelType] = []
    names: List[str] = []
    jsonData = glob.glob(path, recursive=True)
    for jsonPath in jsonData:
        if prefix in jsonPath:
            if reject not in jsonPath:
                f = open(jsonPath, 'r', encoding="utf8")
                data = f.read()
                model = msgspec.json.decode(data, type=modelType)
                names.append(Path(jsonPath).stem)
                models.append(model)

    model_df = {}
    for w, n in zip(models, names):
        model_df[n] = w
    return model_df


# Haven't run datamodel-codegen through python yet. Run in OS.
def createDataModel(f, filename, folder):
    os.makedirs(os.path.dirname(folder), exist_ok=True)
    prefix = Path(filename).stem.rstrip("_")
    command_block = "datamodel-codegen"
    input_block = " --input " + f + " --input-file-type jsonschema "
    output_block = " --output " + folder + str(prefix) + ".py" 
    model_block = " --force-optional --output-model-type msgspec.Struct"

    command = command_block + input_block + output_block + model_block
    subprocess.Popen(command, shell=True)


# Generates a json schema using genjson. Needs to be run on new files.
def createSchema(path, prefix, reject, folder, verbose=False):
    builder = SchemaBuilder()
    jsonData = glob.glob(path, recursive=True)
    for jsonPath in jsonData:
        if prefix in jsonPath:
            if reject not in jsonPath:
                f = open(jsonPath, 'r', encoding="utf8")
                if (verbose):
                    print(jsonPath)
                datastore = json.load(f)
                builder.add_object(datastore)

    schema = builder.to_schema()
    if (verbose):
        print(schema)
    os.makedirs(os.path.dirname(folder), exist_ok=True)
    f = open(folder + prefix + ".json", "w")
    f.write(json.dumps(schema, indent=2))


# Some stuff.
def extractDataframe(model):
    dicts = []
    df_all = []
    for i, k in enumerate(model):
        w = model[k]
        dict = msgspec.json.encode(w)
        dicts.append(dict)
        data = json.loads(dict)
        data = flatten_json(data)
        data = pd.json_normalize(data)
        df_all.append(data)
    df = pd.concat(df_all, axis=0, join='outer')
    return df
