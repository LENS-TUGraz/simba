# -*- coding: utf-8 -*-
"""
Plot hourly forward progress and unavailability along with the irradiance trace
for three full days, based on previously generated simulation data (i.e., in Result_Jan/Jun23).
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import datetime

def hours_to_seconds(hours):
    return hours * 60 * 60

start = hours_to_seconds(0)
end = hours_to_seconds(14)

folder_jun = 'Results_Jun23'
folder_jan = 'Results_Jan23'

df_jun = pd.read_json(f"{folder_jun}/{folder_jun}.json")
df_jan = pd.read_json(f"{folder_jan}/{folder_jan}.json")

labelsize=9
titlesize=9


#%% Plot 'Heatmaps' of hourly forward progress and availabilty for several days

fig, axs = plt.subplots(3, 2, figsize=(6,2.5), gridspec_kw={'width_ratios': [1,0.05]})
axs[2][1].axis('off')

# Select the days we want to plot
days = [27,15,0]
labels = {27:"28/06/23", 
          15:"16/06/23",
          0:"01/01/23"}

df = pd.concat([df_jun[df_jun.day == 27], df_jun[df_jun.day == 15], df_jan[df_jan.day == 0]])
df = df[(df.start_second >= start) & (df.start_second <= end)]

df['Time'] = df.start_second / 3600 + 5 #Transform into hours

# We put everything is bins to have a color scheme that is easier to read
fp_bins=[0, 0.25, 0.5, 0.75, 1]
df['fp_bins'] = pd.cut(df.forward_progress, bins=fp_bins, labels=fp_bins[:-1], include_lowest=True).astype(float)

tu_bins=[0, 1, 5, 10, 10000]
df['tu_bins'] = pd.cut(df.time_unavailable_max, bins=tu_bins, labels=range(0, len(tu_bins)-1), include_lowest=True).astype(float)# tu_bins[1:], 

df_pivoted_fp = df.pivot(columns='Time', index='day', values='forward_progress')
df_pivoted_tu = df.pivot(columns='Time', index='day', values='tu_bins')
df['tu_strings'] = df.time_unavailable_max.apply(lambda x : '{:.2f}'.format(x) if x < 10 else '{:.0f}'.format(x))
df_pivoted_tu_labels = df.pivot(columns='Time', index='day', values='tu_strings')

anot_kws = {'fontsize': 8, 'color':'black'}
sns.heatmap(data=df_pivoted_fp, annot=True, cmap=sns.color_palette('RdYlGn', len(fp_bins) - 1), cbar_ax=axs[0][1], cbar_kws={'boundaries' : fp_bins},  ax=axs[0][0], linewidths=0.02, linecolor='grey', annot_kws=anot_kws, fmt='.2f')
sns.heatmap(data=df_pivoted_tu, annot=df_pivoted_tu_labels, cmap=sns.color_palette('RdYlGn_r', len(tu_bins) - 1), cbar_ax=axs[1][1], cbar_kws={'boundaries' : tu_bins},  ax=axs[1][0], linewidths=0.02, linecolor='grey', fmt='s',  annot_kws=anot_kws)

# Format Color Bar of Forward progress plot
c_bar = axs[0][0].collections[0].colorbar
c_bar.set_ticks([f - 0.125 for f in fp_bins[1:]])
c_bar.set_ticklabels([f'$<${fp_bins[1]}'] + [f"$>${f}" for f in fp_bins[1:-1]], fontsize=labelsize)
c_bar.ax.tick_params(axis='both', which='both', length = 0, pad=0)

# Format Color Bar of Unavailability plot
c_bar = axs[1][0].collections[0].colorbar
c_bar.set_ticks([f + 0.375 for f in c_bar.get_ticks()[:-1]])
c_bar.set_ticklabels([f"$<${f}s" for f in tu_bins[1:-1]] + [f'$>${tu_bins[-2]}s'] , fontsize=labelsize)
c_bar.ax.tick_params(axis='both', which='both', length = 0, pad=0)

# Polish
axs[0][0].set_xticks([])
axs[1][0].set_xticks([])
axs[0][0].set_xlabel("")
axs[1][0].set_xlabel("")
axs[0][0].set_ylabel("")
axs[1][0].set_ylabel("")
axs[0][0].set_yticklabels([f"{labels[int(day.get_text())]}" for day in axs[0][0].get_yticklabels()], fontsize=labelsize,rotation=0)
axs[1][0].set_yticklabels([f"{labels[int(day.get_text())]}" for day in axs[1][0].get_yticklabels()], fontsize=labelsize,rotation=0)
axs[0][0].set_title("(a) Forward progress", fontsize=titlesize,pad=0) 
axs[1][0].set_title("(b) Unavailability (s)", fontsize=titlesize,pad=0) 

#Plot irradiance traces of the same days in third plot
 
for day in days:
    
    if day > 0:
        folder = folder_jun
    else:
        folder = folder_jan
        
    harvester_log = pd.read_pickle(f"{folder}/harvester_log/harvester_log_day{day}.pkl")
    harvester_log = harvester_log[(harvester_log.time >= start) & (harvester_log.time <= end + 3600)]

    harvester_log.time = harvester_log.time + 5*3600
    harvester_log['time_date'] = harvester_log.apply(lambda x : datetime.datetime(2023, 1, 1, 0, 0) + datetime.timedelta(seconds = x.time), axis=1) 

    harvester_log.plot(x='time_date', y='irr', ax=axs[2][0], label=f"{labels[day]}",legend=False, grid=True)
   
axs[2][0].set_xlim([datetime.datetime(2023, 1, 1, 5, 0),datetime.datetime(2023, 1, 1, 20, 0)])
axs[2][0].set_xticks(pd.date_range(start=datetime.datetime(2023, 1, 1, 5, 0), end=datetime.datetime(2023, 1, 1, 20, 0), periods=16), size=labelsize)

xformatter = mdates.DateFormatter('%H')
axs[2][0].xaxis.set_major_formatter(xformatter)
axs[2][0].tick_params(axis='both', which='major', pad=0, labelsize=labelsize,rotation=0)
axs[2][0].tick_params(axis='both', which='minor', pad=0, labelsize=labelsize,rotation=0)
axs[2][0].set_title("(c) Irradiance ($W/m^2$)", fontsize=titlesize,pad=0)   
axs[2][0].set_xlabel("Time (HH)",fontsize=labelsize, labelpad=0)
axs[2][0].set_ylabel('Irradiance\n($W/m^2$)', fontsize=labelsize,labelpad=-2)
h, l = axs[2][0].get_legend_handles_labels()
axs[2][1].legend(h,l, bbox_to_anchor=(1.4,0.5), loc="center", fontsize=labelsize, labelspacing=0, handletextpad=0.1, handlelength=1)

fig.subplots_adjust(top=0.95,
bottom=0.125,
left=0.115,
right=0.91,
hspace=0.33,
wspace=0.05)

fig.savefig("GameboySolar.pdf")

#%% Plot some statstics for overall data

print("Average forward progress for entire month:")
print(f"{df_jun.forward_progress.mean()} (June)")
print(f"{df_jan.forward_progress.mean()} (January)")