#!/usr/bin/env python3

import json
import pandas as pd
from collections import defaultdict
import argparse

if __name__ == '__main__':

    molecules_dict = defaultdict(list)

    df = pd.read_csv("/Users/thomaschan/Desktop/vitessce-data/big-files/input/mermaid.csv")
    for index, row in df.iterrows():
        molecules_dict[row['gene1']].append([row['x'], row['y']])

    with open("/Users/thomaschan/Desktop/molecules.json", 'w') as file:
        json.dump(molecules_dict, file, indent=1)