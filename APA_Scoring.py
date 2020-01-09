
# coding: utf-8

# In[1]:


from __future__ import print_function
from builtins import range
import os
import glob
import sys
import re
import numpy as np
import pandas as pd

out_dir = r'APA_Scores'
All_Scores_out_file = r'APA_Scores_All_Participants.csv'
eprime_text_files = glob.glob("Raw_Data\*.txt")
eprime_text_files_len = len(eprime_text_files)

def etext_to_df(in_file):
    in_dir, infile = os.path.split(in_file)
    filename, suffix = os.path.splitext(infile)
    if suffix == '.txt':
        # Remove first three lines of exported E-Prime tab-delimited text file.
        rem_lines = list(range(3))
        delimiter_ = '\t'
    elif suffix == '.csv':
        # Remove no lines of comma-delimited csv file.
        rem_lines = []
        delimiter_ = ','
    else:
        raise Exception('File not txt or csv: {0}'.format(in_file))

    df = pd.read_csv(in_file, skiprows=rem_lines, sep=delimiter_)
    return df, in_dir, filename


# In[2]:


outcols = ['Subject_ID', 'Age', 'Sex', 'Duration', 'SA_win', 'PA_win', 'SA_RT', 'PA_RT', 'ALL_RT', 'SA_like','PA_like', 'SA_want', 'PA_want', 'IW_SA', 'IW_PA', 'BIAS_SCORE', 'BIAS']
out_df = pd.DataFrame(columns=outcols, index=range(eprime_text_files_len))
os.mkdir(out_dir)


# In[3]:


for out_idx, f in enumerate(eprime_text_files):
    FullData_df, in_dir, filename = etext_to_df(f)
    xml_file = filename+ r'-ExperimentAdvisorReport.xml'
    with open(os.path.join(in_dir, xml_file)) as xmlf:
        xml_str = ''
        for x in range(3):
            xml_str = xmlf.readline().strip()
    dur_str= re.search('<ElapsedTime.*</ElapsedTime', xml_str).group(0)
    Duration = dur_str[28:50]

    idx = FullData_df.index[~FullData_df.condition.isna()].tolist() #obtaining valid indexes - without NaN

    if 'Descriptor[SubTrial]' in FullData_df.columns:
        desc      = 'Descriptor[SubTrial]'
    else:
        desc      = 'Descriptor'

    if 'LeftChoiceDescriptor' in FullData_df.columns:
        leftdesc  = 'LeftChoiceDescriptor'
    else:
        leftdesc  = 'LeftChoiceDescriptor[SubTrial]'

    if 'RightChoiceDescriptor' in FullData_df.columns:
        rightdesc = 'RightChoiceDescriptor'
    else:
        rightdesc = 'RightChoiceDescriptor[SubTrial]'

    if 'LikeWant[SubTrial]' in FullData_df.columns:
        likewant  = 'LikeWant[SubTrial]' 
    else:    
        likewant  = 'LikeWant'

    if 'Scale.RT' in FullData_df.columns:
        scale_rt  = 'Scale.RT'
    else:
        scale_rt  = 'Scale.RT[LogLevel5]'

    if 'Stimulus.RESP[LogLevel5]' in FullData_df.columns:
        stim_resp = 'Stimulus.RESP[LogLevel5]' 
    else:
        stim_resp = 'Stimulus.RESP' 

    if 'Stimulus.RT[LogLevel5]' in FullData_df.columns:
        stim_rt   = 'Stimulus.RT[LogLevel5]'
    else:
        stim_rt   = 'Stimulus.RT'

    Data_df = FullData_df.loc[idx,['condition', 'Subject', 'Age', 'Sex', 'Session', 'SessionDate', 'SessionTime', desc, leftdesc, 'LeftStimulus', rightdesc, 'RightStimulus', likewant, scale_rt, stim_resp, stim_rt]]

    out_file = filename+ r'.csv'
    Data_df.to_csv(os.path.join(out_dir,out_file))

    #Scoring Forced Choice
    SP_FCData_df = Data_df[Data_df['condition'] == 'SP'].iloc[:, [14, 15, 9, 11 ]]

    def activity_label(row):
        if row[0] == 1.0:
            activity = row[2]
            return activity[0:2]
        elif row[0] == 2.0:
            activity = row[3]
            return activity[0:2]

    SP_FCData_df ['Activity'] = SP_FCData_df.apply (lambda row: activity_label(row), axis=1)
   
    SA_win = len(SP_FCData_df[SP_FCData_df['Activity'] == 'SA'])
    PA_win = len(SP_FCData_df[SP_FCData_df['Activity'] == 'PA'])
    ALL_RT = SP_FCData_df.iloc[:,[1]].mean()
    SA_RT = SP_FCData_df[SP_FCData_df['Activity'] == 'SA'].iloc[:,[1]].mean()
    PA_RT = SP_FCData_df[SP_FCData_df['Activity'] == 'PA'].iloc[:,[1]].mean()

    #Scoring Liking
    LVM_Data_df = Data_df[Data_df.iloc[:,12] == 'Like very much'].iloc[:, [0, 14]]

    SA_like = LVM_Data_df[LVM_Data_df['condition'].str.contains('SA', regex=False)].iloc[:,[1]].mean()
    PA_like = LVM_Data_df[LVM_Data_df['condition'].str.contains('PA', regex=False)].iloc[:,[1]].mean()

    #Scoring Wanting
    WVM_Data_df = Data_df[Data_df.iloc[:,12] == 'Want very much'].iloc[:, [0, 14]]

    SA_want = WVM_Data_df[WVM_Data_df['condition'].str.contains('SA', regex=False)].iloc[:,[1]].mean()
    PA_want = WVM_Data_df[WVM_Data_df['condition'].str.contains('PA', regex=False)].iloc[:,[1]].mean()

    # Implicit Wanting (IW) and BIAS_SCORE Calculations
    IW_SA = (SA_win * (ALL_RT / SA_RT)) - (PA_win * (ALL_RT / PA_RT))
    IW_PA = (PA_win * (ALL_RT / PA_RT)) - (SA_win * (ALL_RT / SA_RT))
    BIAS_SCORE = IW_SA - IW_PA

    if BIAS_SCORE.item() > 0: #Use .item() for boolean operations on single element series
        BIAS = 'SA'
    elif BIAS_SCORE.item() < 0:
        BIAS = 'PA'
    else:
        BIAS = 'No Bias'
   
    outrow = [Data_df.iloc[0]['Subject'], Data_df.iloc[0]['Age'], Data_df.iloc[0]['Sex'], Duration, SA_win, PA_win, SA_RT.item(), PA_RT.item(), ALL_RT.item(), SA_like.item(), PA_like.item(), SA_want.item(), PA_want.item(), IW_SA.item(), IW_PA.item(), BIAS_SCORE.item(), BIAS]

    out_df.loc[out_idx] = outrow
  


# In[4]:


out_df.to_csv(os.path.join(out_dir,All_Scores_out_file))

