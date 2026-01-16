# Import python packages
import streamlit as st
import pandas as pd
import numpy as np
from snowflake.snowpark.context import get_active_session

# Write directly to the app
st.title(f"Permit Data Dashboard")
st.set_page_config(layout='wide')
# Get the current credentials
session = get_active_session()

@st.cache_data
def obtain_data():
    permits=session.sql('''select pcis_permit_num, status, status_date, year(status_date) as status_year,
    permit_type, permit_sub_type, initiating_office, issue_date, year(issue_date) as issue_year 
    ,zip_code,ai_description,valuation,license_num,contractor_business_name,license_type,
    latitude_longitude
    from la_permit_data.public.permit_records;''').to_pandas()
    permits['ISSUE_DATE']=pd.to_datetime(permits['ISSUE_DATE'])
    permits['VALUATION']=pd.to_numeric(permits['VALUATION'].str.replace(r'[$,]','',regex=True))
    permits[['LONGITUDE','LATITUDE']]=permits['LATITUDE_LONGITUDE'].str.extract(r'\(([^\s]+)\s([^\s]+)\)')
    permits['LONGITUDE']=pd.to_numeric(permits['LONGITUDE'],errors='coerce')
    permits['LATITUDE']=pd.to_numeric(permits['LATITUDE'],errors='coerce')
    permits['DAYS_ELAPSED']=(permits['STATUS_DATE']-permits['ISSUE_DATE']).dt.days
    permits.loc[permits['STATUS']=='Issued','DAYS_ELAPSED']=np.nan
    licenses=session.sql('''select license_no, business_name, mailing_address, city, zip_code, 
    business_phone, classifications, issue_date from la_permit_data.public.master_license 
    where license_no in (select distinct license_num from la_permit_data.public.permit_records)''').to_pandas().set_index('LICENSE_NO')
    return permits,licenses
permits,licenses=obtain_data()


date0=permits['ISSUE_YEAR'].min()
date1=permits['ISSUE_YEAR'].max()
options={}
filters=['STATUS','PERMIT_TYPE','PERMIT_SUB_TYPE','ZIP_CODE']
for col in filters:
    options[col]=permits[col].value_counts().index
v0=permits['VALUATION'].min()
v1=permits['VALUATION'].max()

st.sidebar.header('Filters')
min_year,max_year=st.sidebar.slider('Issue Year Range', date0, date1, value=(date0,date1))
values={}
for col in filters:
    values[col]=st.sidebar.multiselect(col.title(), options=options[col])

contains=st.sidebar.text_input('Description Contains:')
excludes=st.sidebar.text_input('Description Excludes:')

@st.cache_data
def filter_data(min_year,max_year,values,contains,excludes):
    df=permits[permits['ISSUE_YEAR'].between(min_year,max_year)]
    for col in filters:
        if len(values[col])>0:
            df=df[df[col].isin(values[col])]
    if contains:
        df=df[df['AI_DESCRIPTION'].fillna("").str.contains(contains)]
    if excludes:
        df=df[~df['AI_DESCRIPTION'].fillna("").str.contains(excludes)]
        
    top=df[df['LICENSE_NUM']!='0'].groupby('LICENSE_NUM')\
    .agg(NAME=('CONTRACTOR_BUSINESS_NAME','first'),
        NUM_PERMITS=('PCIS_PERMIT_NUM','nunique'),
         NUM_ZIPCODES=('ZIP_CODE','nunique'),
         MEDIAN_DAYS=('DAYS_ELAPSED', 'median'),
         MED_VALUATION=('VALUATION','median')
        )
    time = df.groupby(pd.Grouper(key="ISSUE_DATE", freq="M"))['PCIS_PERMIT_NUM'].count()
    office=df.groupby('INITIATING_OFFICE')['PCIS_PERMIT_NUM'].nunique()
    return df,top,time,office

df,top,time,office=filter_data(min_year,max_year,values,contains,excludes)

col1,col2=st.columns(2)
with col1:
    st.metric('Total permits', len(df))
    st.subheader('By Issue Dates')
    st.line_chart(time,height=200)
with col2:
    st.metric('Total contractors',df['LICENSE_NUM'].nunique())
    st.subheader('By Initiating Office')
    st.bar_chart(office,height=200)



st.subheader('Associated Contractors')
top=top.sort_values(by='NUM_PERMITS',ascending=False)
st.dataframe(top,height=200)

