# -*- coding: utf-8 -*-
"""
Created on Fri Aug  7 15:25:06 2020

@author: António Oliveira
"""
#Task: GYANT Data Analyst Take-Home Assignment
import pandas as pd
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Frame, Spacer, Image, Table, TableStyle, SimpleDocTemplate
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing#, string
from reportlab.graphics.charts.textlabels import Label
from reportlab.graphics.charts.legends import Legend
from reportlab.platypus import Image
from datetime import datetime, timedelta
import numpy as np
from io import StringIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython import get_ipython
import json
author='António Oliveira'
typeA='Client A'
typeB='Client B'
typeC='Client C'
styles = getSampleStyleSheet()
styleN = styles['Normal']
def count_users(df):
    n_users=df.drop_duplicates(subset=['User Id']).shape[0]
    return n_users
def report_template_part1(logo=None,title=None,author_date=None,inputs=None,trend_analysis=None,user_type=None,df=None):
 # create a list and add the elements of our document (image, paragraphs, table, chart) to it
    story=[]
    #define the style for our paragraph text
    #First add the Gyant Logo
    im = Image(logo, width=1*inch, height=1*inch)
    im.hAlign = 'CENTER'
    story.append(im)
    #add the title
    story.append(Paragraph(title,styleN))
    story.append(Spacer(1,.25*inch))
    #Add author and date of the report
    story.append(Paragraph(author_date,styleN))
    story.append(Spacer(1,.25*inch))
    #Add dataset names
    story.append(Paragraph(inputs,styleN))
    story.append(Spacer(1,.25*inch))
    #Add t
    story.append(Paragraph(trend_analysis,styleN))
    story.append(Spacer(1,.25*inch))
    #Number of users
    story.append(Paragraph("Number of users of %s type: %d" % (user_type,count_users(df)),styleN))
    story.append(Spacer(1,.25*inch))    
    return story

def get_user_type_counts(df,date_ini,step,screen_list):
    date_end=date_ini+timedelta(days=step)
    df=df[(df['Session_begin']>date_ini) & (df['Session_begin']<date_end)]
    if len(df)==0:
        return [0,0,0,0],[0,0],0,[0,0,0,0,0,0],0
    #only screening
    df.FAQ=df.FAQ.fillna('Screen')
    df_gr=df.groupby(['User Id','FAQ']).size().reset_index().rename(columns={0:'count'})
    pv_users=pd.pivot_table(df_gr,index='User Id', columns='FAQ',aggfunc=np.sum,fill_value=0,margins='True')    
    pv_users=pv_users.drop('All',axis=0)
    column_screen=('count',                               'Screen')
    column_end=('count',                               'end')
    column_All=('count',                               'All')    
    users_only_screen=0
    users_screen_and_faq=0
    users_only_faq=0
    n_users_screen_end=0
    if column_end in pv_users:
        users_screen_and_faq=len(pv_users[(pv_users[column_All]>pv_users[column_end]) & (pv_users[column_end]>0)])
        n_users_screen_end=len(pv_users[pv_users[column_end]>0])
    if (column_end in pv_users and column_screen in pv_users):
        users_only_screen=len(pv_users[pv_users[column_screen]+pv_users[column_end]==pv_users[column_All]])
        users_only_faq=len(pv_users[(pv_users[column_end]==0) & (pv_users[column_screen]==0) & (pv_users[column_All]>0)])
    screen_rate=0    
    if (n_users_screen_end+users_only_screen)>0:
        screen_rate=n_users_screen_end/(n_users_screen_end+users_only_screen)*100
    care_type={'callNurseLine':0,'callDoctorOrTelemed':0,'goToFmgTriage':0,'call911':0,'callAheadER':0,'goToER':0}
    unique_user=df['User Id'].unique()
    users_filtered=[]
    for id_u in unique_user:
        users_filtered.append([i for i in screen_list if id_u==i['user']['id']])
    for t in care_type:
        for i in range(len(users_filtered)):
                try:
                    if users_filtered[i][0]['userContent']['covidMessages']['messages'][t]==True:
                        care_type[t]+=1
                except:
                    #key is not detected
                    pass             
    return [users_only_screen, users_screen_and_faq, users_only_faq,users_only_screen+users_screen_and_faq+users_only_faq],[n_users_screen_end,users_only_screen],screen_rate,[v for k,v in care_type.items()],len(df[(df['FAQ']!='Screen') & (df['FAQ']!='end')]['FAQ'])


def screen_list_to_json(screen_list):
    screen_list=[json.loads(i) for i in screen_list]
    return screen_list
#Report Type: Daily report
#Customer type: Client A
def daily_report(users,faqs,begin_date,end_date,screen_list):
    #scope users dataframe period
    story=report_template_part1(logo='Gyant.jpg',title="<strong>Home assignment: Daily report (Data analysis for Coronavirus pandemic for Client A type) </strong>",
    author_date="Report Author: %s / Report Date: %s" % (author,datetime.today().strftime('%Y-%m-%d')),inputs="Input datasets: [users.csv, faqs.csv, screenings.json]",
    trend_analysis="Trend analysis daily basis: from %s to %s" % (begin_date,end_date), user_type='Client A',df=users)
    #prepare table for users type
    #Number of users    
    story.append(Paragraph("User type trend chart:",styleN))
    story.append(Spacer(1,.25*inch))
    #obtain the user types
    delta=timedelta(days=1)
    users_check=[]
    step=1
    users_check={}
    screen_check={}
    screen_rate={}
    care_type={}
    n_faqs={}
    begin_date-=timedelta(days=1)
    while begin_date<=(end_date)-timedelta(days=step):
        users_check[begin_date+delta], screen_check[begin_date+delta],screen_rate[begin_date+delta],care_type[begin_date+delta],n_faqs[begin_date+delta]=get_user_type_counts(faqs,begin_date,step,screen_list)
        begin_date += delta
    users_check=pd.DataFrame.from_dict(users_check, orient='index')
    users_check.columns=['screen_only','screen_vs_faq','faq_only','total_users']
    trend_plot=users_check.plot.line()
    plt.ylabel('Number trend daily')
    trend_plot.figure.savefig('daily.png')
    story.append(Image('daily.png',300,175))
    story.append(Paragraph(" ",styleN))
    story.append(Spacer(1,.25*inch))    
    #Screen analisys
    story.append(Paragraph("Screen completed vs uncompleted chart:",styleN))
    story.append(Spacer(1,.25*inch))
    screen_check=pd.DataFrame.from_dict(screen_check, orient='index')
    #import pdb; pdb.set_trace()
    screen_check.columns=['Completed Screening','Uncompleted Screening']
    #users_check['day']=users_check.index.day
    screen_check=screen_check.plot.line()
    plt.ylabel('Number trend daily')
    screen_check.figure.savefig('screen_daily.png')
    #import pdb; pdb.set_trace()
    story.append(Image('screen_daily.png',300,175))
    story.append(Paragraph(" ",styleN))
    #Screen rate analisys
    story.append(Paragraph("Screen rate completion chart:",styleN))
    story.append(Spacer(1,.25*inch))
    screen_rate=pd.DataFrame.from_dict(screen_rate, orient='index')
    screen_rate.columns=['Screen rate [%]']
    #users_check['day']=users_check.index.day
    screen_rate=screen_rate.plot.line()
    plt.ylabel('Rate trend daily')
    screen_rate.figure.savefig('screen_rate.png')
    story.append(Image('screen_rate.png',300,175))
    story.append(Paragraph(" ",styleN))
    story.append(Spacer(1,.25*inch))   
    #convert care_type to dataframe
    story.append(Paragraph("Care type analysis :",styleN))
    story.append(Spacer(1,.25*inch))
    care_type=pd.DataFrame.from_dict(care_type, orient='index')
    care_type.columns=['callNurseLine','callDoctorOrTelemed','goToFmgTriage','call911','callAheadER','goToER']
    care_type_plot=care_type.plot.line()
    plt.ylabel('Number trend daily')
    care_type_plot.figure.savefig('care_type_daily.png')
    story.append(Image('care_type_daily.png',300,175))
    
    story.append(Paragraph(" ",styleN))
    story.append(Spacer(1,.25*inch))   
    #convert care_type to dataframe
    story.append(Paragraph("Number FAQS answered:",styleN))
    story.append(Spacer(1,.25*inch))
    n_faqs=pd.DataFrame.from_dict(n_faqs, orient='index')
    n_faqs.columns=['N_FAQS']
    n_faqs_plot=n_faqs.plot.line()
    plt.ylabel('Number trend daily')
    n_faqs_plot.figure.savefig('n_faqs_daily.png')
    story.append(Image('n_faqs_daily.png',300,175))
    
    #build our document with the list of flowables we put together
    doc = SimpleDocTemplate('daily_report.pdf',pagesize = letter, topMargin=0)
    doc.build(story)
def weekly_report(users,faqs,begin_date,end_date,screen_list):
    #scope users dataframe period
    story=report_template_part1(logo='Gyant.jpg',title="<strong>Home assignment: Monthly report (Data analysis for Coronavirus pandemic for Client B type) </strong>",
    author_date="Report Author: %s / Report Date: %s" % (author,datetime.today().strftime('%Y-%m-%d')),inputs="Input datasets: [users.csv, faqs.csv, screenings.json]",
    trend_analysis="Trend analysis (8 days mean): from %s to %s" % (begin_date,end_date), user_type='Client B',df=users)
    #prepare table for users type
    #Number of users    
    #obtain the user types
    delta=timedelta(days=1)
    users_check=[]
    step=1
    users_check={}
    begin_date-=timedelta(days=1)
    screen_check={}
    screen_rate={}
    care_type={}
    n_faqs={}
    while begin_date<=(end_date)-timedelta(days=step):
        users_check[begin_date+delta],screen_check[begin_date+delta],screen_rate[begin_date+delta],care_type[begin_date+delta],n_faqs[begin_date+delta]=get_user_type_counts(faqs,begin_date,step,screen_list)
        begin_date += delta
    users_check=pd.DataFrame.from_dict(users_check, orient='index')
    story.append(Paragraph("User type trend chart weekly basis:",styleN))
    story.append(Spacer(1,.25*inch))
    #users_check_trend=pd.DataFrame(users_check['total_users'].rolling(window=8,center=True).mean())
    users_check_trend=pd.DataFrame()
    users_check_trend[['screen_only','screen_vs_faq','faq_only','total_users']]=users_check.rolling(window=8,center=True).mean()
    #users_check['day']=users_check.index.day
    trend_plot=users_check_trend.plot.line()
    plt.ylabel('Number trend [8 days]')
    trend_plot.figure.savefig('weekly_trend.png')
    story.append(Image('weekly_trend.png',300,175))
    story.append(Paragraph(" ",styleN))
    story.append(Spacer(1,.25*inch))    
    #Screen analisys
    story.append(Paragraph("Screen completed vs uncompleted chart weekly basis:",styleN))
    story.append(Spacer(1,.25*inch))
    screen_check=pd.DataFrame.from_dict(screen_check, orient='index')
    #screen_check.columns=['Complete Screening','Uncompleted Screening']
    screen_check_trend=pd.DataFrame()
    screen_check_trend[['Completed Screening','Uncompleted Screening']]=screen_check.rolling(window=8,center=True).mean()                         
    screen_check_trend=screen_check_trend.plot.line()
    plt.ylabel('Number trend [8 days]')
    screen_check_trend.figure.savefig('screen_weekly.png')
    story.append(Image('screen_weekly.png',300,175))
    story.append(Paragraph(" ",styleN))
    story.append(Spacer(1,.25*inch))    
    #Screen rate analisys
    screen_rate=pd.DataFrame.from_dict(screen_rate, orient='index')
    screen_rate_trend=pd.DataFrame()
    screen_rate_trend[['Completed rate [%]']]=screen_rate.rolling(window=8,center=True).mean()             
    story.append(Paragraph("Screen rate completion chart weekly basis:",styleN))
    story.append(Spacer(1,.25*inch))
    #users_check['day']=users_check.index.day
    screen_rate_trend=screen_rate_trend.plot.line()
    plt.ylabel('Rate trend [8 days]')
    screen_rate_trend.figure.savefig('screen_rate_weekly.png')
    story.append(Image('screen_rate_weekly.png',300,175))
    
    story.append(Paragraph(" ",styleN))
    story.append(Spacer(1,.25*inch))    
    #convert care_type to dataframe
    story.append(Paragraph("Care type analysis:",styleN))
    story.append(Spacer(1,.25*inch))
    care_type=pd.DataFrame.from_dict(care_type, orient='index')
    care_type_trend=pd.DataFrame()
    care_type_trend=care_type.rolling(window=8,center=True).mean()  
    care_type_trend.columns=['callNurseLine','callDoctorOrTelemed','goToFmgTriage','call911','callAheadER','goToER']
    care_type_plot=care_type_trend.plot.line()
    plt.ylabel('Number trend [8 days]')
    care_type_plot.figure.savefig('care_type_weekly.png')
    #users_check['day']=users_check.index.day
    story.append(Image('care_type_weekly.png',300,175))
    story.append(Paragraph(" ",styleN))
    story.append(Spacer(1,.25*inch))   
    story.append(Paragraph("Number FAQS answered:",styleN))
    story.append(Spacer(1,.25*inch))
    n_faqs=pd.DataFrame.from_dict(n_faqs, orient='index')
    n_faqs_trend=pd.DataFrame()
    n_faqs_trend=n_faqs.rolling(window=8,center=True).mean()  
    n_faqs_trend.columns=['N_FAQS']
    n_faqs_plot=n_faqs_trend.plot.line()
    plt.ylabel('Number trend [8 days]')
    n_faqs_plot.figure.savefig('n_faqs_weekly.png')
    story.append(Image('n_faqs_weekly.png',300,175))
    #build our document with the list of flowables we put together
    doc = SimpleDocTemplate('weekly_report.pdf',pagesize = letter, topMargin=0)
    doc.build(story)   
#
def alltime_report(users,faqs,begin_date,end_date,screen_list):
#scope users dataframe period
    story=report_template_part1(logo='Gyant.jpg',title="<strong>Home assignment: Complete period (Data analysis for Coronavirus pandemic for Client C type) </strong>",
    author_date="Report Author: %s / Report Date: %s" % (author,datetime.today().strftime('%Y-%m-%d')),inputs="Input datasets: [users.csv, faqs.csv, screenings.json]",
    trend_analysis="Trend analysis (31 days mean): from %s to %s" % (begin_date,end_date), user_type='Client C',df=users)
    #prepare table for users type
    #Number of users    
    #obtain the user types
    delta=timedelta(days=1)
    users_check=[]
    step=1
    users_check={}
    begin_date-=timedelta(days=1)
    screen_check={}
    screen_rate={}
    care_type={}
    n_faqs={}
    while begin_date<=(end_date)-timedelta(days=step):
        users_check[begin_date+delta],screen_check[begin_date+delta],screen_rate[begin_date+delta],care_type[begin_date+delta],n_faqs[begin_date+delta]=get_user_type_counts(faqs,begin_date,step,screen_list)
        begin_date += delta
    story.append(Paragraph("User type trend chart:",styleN))
    story.append(Spacer(1,.25*inch))
    users_check=pd.DataFrame.from_dict(users_check, orient='index')
    story.append(Paragraph("User type trend chart Monthly basis:",styleN))
    story.append(Spacer(1,.25*inch))
    users_check_trend=pd.DataFrame()
    users_check_trend[['screen_only','screen_vs_faq','faq_only','total_users']]=users_check.rolling(window=31,center=True).mean()
    trend_plot=users_check_trend.plot.line()
    plt.ylabel('Number trend [31 days]')
    trend_plot.figure.savefig('monthly_trend.png')
    story.append(Image('monthly_trend.png',300,175))
    story.append(Paragraph(" ",styleN))
    story.append(Spacer(1,.25*inch))    
    #Screen analisys
    story.append(Paragraph("Screen completed vs uncompleted chart Monthly basis:",styleN))
    story.append(Spacer(1,.25*inch))
    screen_check=pd.DataFrame.from_dict(screen_check, orient='index')
    #screen_check.columns=['Complete Screening','Uncompleted Screening']
    screen_check_trend=pd.DataFrame()
    screen_check_trend[['Complete Screening','Uncompleted Screening']]=screen_check.rolling(window=31,center=True).mean()                         
    screen_check_trend=screen_check_trend.plot.line()
    plt.ylabel('Number trend [31 days]')
    screen_check_trend.figure.savefig('screen_monthly.png')
    story.append(Image('screen_monthly.png',300,180))
    story.append(Paragraph(" ",styleN))
    story.append(Spacer(1,.25*inch))    
    #Screen rate analisys
    screen_rate=pd.DataFrame.from_dict(screen_rate, orient='index')
    screen_rate_trend=pd.DataFrame()
    screen_rate_trend[['Completed rate [%]']]=screen_rate.rolling(window=31,center=True).mean()             
    story.append(Paragraph("Screen rate completion chart Monthly basis:",styleN))
    story.append(Spacer(1,.25*inch))
    #users_check['day']=users_check.index.day
    screen_rate_trend=screen_rate_trend.plot.line()
    plt.ylabel('Rate trend [31 days]')
    screen_rate_trend.figure.savefig('screen_rate_monthly.png')
    story.append(Image('screen_rate_monthly.png',300,175))
    story.append(Paragraph(" ",styleN))
    story.append(Spacer(1,.25*inch))    
    #convert care_type to dataframe
    story.append(Paragraph("Care type analysis Monthly basis:",styleN))
    story.append(Spacer(1,.25*inch))
    care_type=pd.DataFrame.from_dict(care_type, orient='index')
    care_type_trend=pd.DataFrame()
    care_type_trend=care_type.rolling(window=31,center=True).mean()  
    care_type_trend.columns=['callNurseLine','callDoctorOrTelemed','goToFmgTriage','call911','callAheadER','goToER']
    care_type_plot=care_type_trend.plot.line()
    plt.ylabel('Number trend [31 days]')
    care_type_plot.figure.savefig('care_type_monthly.png')
    #users_check['day']=users_check.index.day
    story.append(Image('care_type_monthly.png',300,175))
    story.append(Paragraph(" ",styleN))
    story.append(Spacer(1,.25*inch))   
    story.append(Paragraph("Number FAQS answered:",styleN))
    story.append(Spacer(1,.25*inch))
    n_faqs=pd.DataFrame.from_dict(n_faqs, orient='index')
    n_faqs_trend=pd.DataFrame()
    n_faqs_trend=n_faqs.rolling(window=31,center=True).mean()  
    n_faqs_trend.columns=['N_FAQS']
    n_faqs_plot=n_faqs_trend.plot.line()
    plt.ylabel('Number trend [31 days]')
    n_faqs_plot.figure.savefig('n_faqs_monthly.png')
    story.append(Image('n_faqs_monthly.png',300,175))
    
    #build our document with the list of flowables we put together
    doc = SimpleDocTemplate('all_time_report.pdf',pagesize = letter, topMargin=0)
    doc.build(story)   
def filter_users(users,faqs,type):
    #filter users by Client type in users dataset
    users_filtered=users[users['Client']==type]
    #filter users by Client type in faqs dataset
    faqs_filtered=pd.merge(faqs, users_filtered, on=['User Id'], how='right')
    return users_filtered,faqs_filtered
if __name__ == '__main__':
    #users dataframe    
    dateparse = lambda x: pd.datetime.strptime(x[:19], '%Y-%m-%d %H:%M:%S')
    users=pd.read_csv(r'C:\Users\amaol\AnacondaProjects\Home_assignment\data_analyst_assignment\users.csv',
                      parse_dates={'Session_begin': ['Session Time (UTC)'],'Session_end': ['Session End Time (UTC)']}, date_parser=dateparse)
    #faqs dataframe
    faqs=pd.read_csv(r'C:\Users\amaol\AnacondaProjects\Home_assignment\data_analyst_assignment\faqs.csv')
    #read json
    with open(r'C:\Users\amaol\AnacondaProjects\Home_assignment\data_analyst_assignment\screenings.json') as f:
        screen_list=['{' + word + '}'for line in f for word in line.split("},{")]
    screen_list=screen_list_to_json(screen_list)
    users=users.sort_values(by=['Session_begin'])
    #Client A report
    end_date=datetime(2020,4,22)
    begin_date=end_date-timedelta(days=7)  
    #client A dataset filtering
    users_A,faqs_A=filter_users(users[(users['Session_begin']>begin_date) & (users['Session_begin']<end_date)],faqs,'Client A')
    daily_report(users_A,faqs_A,begin_date,end_date,screen_list)
    #Client B report
    end_date=datetime(2020,6,1)
    begin_date=end_date-timedelta(days=31)  
    #client B dataset filtering
    users_B,faqs_B=filter_users(users[(users['Session_begin']>begin_date) & (users['Session_begin']<end_date)],faqs,'Client B')
    weekly_report(users_B,faqs_B,begin_date,end_date,screen_list)
    end_date=datetime(2020,6,1)
    begin_date=datetime(2020,3,13)  
    #import pdb; pdb.set_trace()
    #client C dataset filtering
    users_C,faqs_C=filter_users(users[(users['Session_begin']>begin_date) & (users['Session_begin']<end_date)],faqs,'Client C')
    alltime_report(users_C,faqs_C,begin_date,end_date,screen_list)
    
    



