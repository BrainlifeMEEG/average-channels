"""
Average PSD values across a selected set of channels.

This app loads a per-channel PSD table (TSV), averages the selected
channels together, and saves the averaged spectrum plus a plot.

Inputs:
    - psd: Path to per-channel PSD TSV file
    - new_name: Name to give the averaged channel row
    - channel_list: Channels to average, as a bracketed comma-separated string

Outputs:
    - out_dir/psd.tsv: Averaged PSD table
    - out_figs/avg_channels.png: Averaged PSD plot
    - product.json: Metadata about the averaging
"""

# Copyright (c) 2026 brainlife.io
#
# Author: Guiomar Niso

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brainlife_utils'))

# Standard imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Import shared utilities
from brainlife_utils import (
    load_config,
    setup_matplotlib_backend,
    ensure_output_dirs,
    create_product_json,
    add_info_to_product,
    add_image_to_product,
    require_config_keys
)

# Set up matplotlib for headless execution
setup_matplotlib_backend()

# Ensure output directories exist
ensure_output_dirs('out_dir', 'out_figs')

# Load configuration
config = load_config()
require_config_keys(config, ['psd', 'new_name', 'channel_list'])

# == GET CONFIG VALUES ==
fname = config['psd']
new_name = config['new_name']
channel_list1 = config['channel_list']
channel_list = channel_list1.replace('[', '').replace(']', '').split(", ")

# == LOAD DATA ==
df_psd = pd.read_csv(fname, sep='\t')

# Get only selected channels
sel_data = df_psd[df_psd.channels.isin(channel_list)].copy()

# Average channels
avd_data = np.mean(sel_data, axis=0)
std_data = np.std(sel_data, axis=0)

# Channels averaged
chin = list(set(sel_data.channels).intersection(set(channel_list)))
chout = list(set(sel_data.channels).difference(set(channel_list)))
print('- Channels averaged (', len(chin), '):', *chin, sep=' ')
print('- Channels not found (', len(chout), '):', *chout, sep=' ')

# == SAVE FILE ==
df_psd_avg = pd.DataFrame(avd_data, columns=[new_name]).transpose()
df_psd_avg.index.name = 'channels'
df_psd_avg.columns.name = 'freqs'
df_psd_avg.to_csv(os.path.join('out_dir', 'psd.tsv'), sep='\t')

# List of frequencies
freqs = df_psd_avg.columns.to_numpy()
freqs = freqs.astype(float)

# == FIGURE ==
plt.figure(1)
plt.plot(freqs, avd_data)
plt.xticks(freqs[::40])  # take every 40th value in 'freqs'
plt.fill_between(freqs, avd_data + std_data, avd_data - std_data, facecolor='blue', alpha=0.2)
plt.grid(visible=1, alpha=0.5)
plt.xlim(freqs[0], freqs[-1])
plt.xlabel('frequency [Hz]')
plt.ylabel('PSD')
plt.title('Averaged PSD')
ax = plt.subplot(111)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

fig_path = os.path.join('out_figs', 'avg_channels.png')
plt.savefig(fig_path)
plt.close()

# == CREATE PRODUCT.JSON ==
product_items = []
add_info_to_product(product_items, f'Averaged {len(chin)} channels into "{new_name}"', 'success')
if chout:
    add_info_to_product(product_items, f'{len(chout)} requested channels not found in input', 'warning')
add_image_to_product(product_items, 'Averaged PSD', filepath=fig_path)
create_product_json(product_items)
