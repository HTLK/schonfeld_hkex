#class HKEXDataPull(stock_code, year, month, day):
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

class HKEXInput():

    def __init__(self, stock_code, start_date, end_date, chg_threshold = None):
        
        """
        Parameters
        ----------
        stock_code : str
            HK Stock Code
        start_date : str
            Start date of analysis
        end_date : str
            End date of analysis
        chg_threshold : float, optional
            Threshold used to identify transactions between parties
        """
        
        self.stock_code = stock_code
        self.start_date = start_date
        self.end_date = end_date

        if chg_threshold != None:
            self.chg_threshold = chg_threshold
        else:
            self.chg_threshold = None
            print('Warning: HKEXInput object instanced with chg_threshold set as None.')

class HKEXConnection():

    def __init__(self, user_input: HKEXInput):
        
        """
        Parameters
        ----------
        user_input : HKEXInput
            HKEXInput object containing details of analysis
        """

        from selenium import webdriver
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Initiate Web Instance
        print('Initiating connection to HKEX...')
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        
        # Install Chrome Driver
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options = options)
        
        # Open HKEX website
        self.driver.get("https://www3.hkexnews.hk/sdw/search/searchsdw.aspx")
        
        self.user_input = user_input

    def setStockCode(self):
        
        """Sets the stock code to be utilized for the analysis"""
        
        # Find HTML element tagged as txtStockCode and change value
        self.driver.find_element("name", "txtStockCode").send_keys(self.user_input.stock_code)

    def setDate(self, current_analysis_date = None):

        from selenium.webdriver.common.by import By

        if current_analysis_date == None:
            self.current_analysis_date = self.user_input.end_date
        
        # Find HTML element containing the date of data collected and manipulate value attribute
        date_element = self.driver.find_element(By.CSS_SELECTOR, "input#txtShareholdingDate")
        self.driver.execute_script("arguments[0].setAttribute('value','"+ self.current_analysis_date +"')", date_element)

    def runAnalysis(self):
        
        """Runs shareholding analysis as of end date"""
        
        from selenium.webdriver.common.by import By
        
        # Set stock code
        self.setStockCode()

        print('Extracting data for stock code '+ self.user_input.stock_code +' as of date '+ self.current_analysis_date)

        # Execute javascript to display data
        self.driver.find_element("id", "btnSearch").click()
        
        # Retrieve data from HTML source
        shareholding_data = pd.read_html(self.driver.page_source)[0]
        
        # Rename columns
        shareholding_data.columns = ['participant_id',
                                     'participant_name',
                                     'participant_address',
                                     'participant_shares',
                                     'participant_pct_holding'
                                     ]
        
        # Clean data from unnecessary taggings
        shareholding_data['participant_id']          = shareholding_data['participant_id'].str.slice(start = 16)
        shareholding_data['participant_name']        = shareholding_data['participant_name'].str.slice(start = 69)
        shareholding_data['participant_address']     = shareholding_data['participant_address'].str.slice(start = 9)
        shareholding_data['participant_shares']      = shareholding_data['participant_shares'].str.slice(start = 14)
        shareholding_data['participant_shares']      = shareholding_data['participant_shares'].str.replace(',','').astype(float)
        shareholding_data['participant_pct_holding'] = shareholding_data['participant_pct_holding'].str.slice(start = 57)
        
        # Find total issue for selected stock code
        total_issue = float(self.driver.find_element(By.XPATH, "//div[contains(@class,'summary-value')]")
                            .text
                            .replace(',','')
                            )
        
        # Re-calculate % Holding as WebPage data has less precision
        shareholding_data['participant_pct_holding'] = shareholding_data['participant_shares'] / total_issue
        
        # Sort values by % holding
        shareholding_data = shareholding_data.sort_values(by='participant_pct_holding', ascending = False)

        self.shareholding_data = shareholding_data

    def runChangeAnalysis(self):
        
        """Runs shareholding analysis between two dates and generates DataFrame containing summary of transactions above threshold"""

        from pandas.tseries.offsets import BDay
        from selenium.webdriver.common.by import By
        
        # Extract business days between start and end date
        bdays = pd.date_range(self.user_input.start_date,
                              self.user_input.end_date,
                              freq=BDay()
                              ).strftime('%Y/%m/%d').values

        # Set stock code
        self.setStockCode()
        
        # Initialize DataFrame for analysis
        shareholding_data = pd.DataFrame(columns=['participant_id',
                                                  'participant_name',
                                                  'participant_address',
                                                  'participant_shares',
                                                  'participant_pct_holding',
                                                  'date'
                                                  ])
        
        # Iterate through all business days
        for d in bdays:
            print('Extracting data for stock code '+
                  self.user_input.stock_code +
                  ' as of date '+
                  d
                  )
            
            # Change date input in HKEX website
            date_element = self.driver.find_element(By.CSS_SELECTOR,
                                               "input#txtShareholdingDate")
            
            # Collect data from website
            self.driver.execute_script("arguments[0].setAttribute('value','"+ d +"')", date_element)

            del date_element

            # Execute javascript to display data
            self.driver.find_element("id", "btnSearch").click()
            
            # Read HTML source data
            temp_shareholding_data = pd.read_html(self.driver.page_source)[0]

            temp_shareholding_data.columns = ['participant_id',
                                         'participant_name',
                                         'participant_address',
                                         'participant_shares',
                                         'participant_pct_holding'
                                         ]
            
            # Clean raw HTML data into structured DataFrame
            temp_shareholding_data['participant_id']          = temp_shareholding_data['participant_id'].str.slice(start = 16)
            temp_shareholding_data['participant_name']        = temp_shareholding_data['participant_name'].str.slice(start = 69)
            temp_shareholding_data['participant_address']     = temp_shareholding_data['participant_address'].str.slice(start = 9)
            temp_shareholding_data['participant_shares']      = temp_shareholding_data['participant_shares'].str.slice(start = 14)
            temp_shareholding_data['participant_shares']      = temp_shareholding_data['participant_shares'].str.replace(',','').astype(float)
            temp_shareholding_data['participant_pct_holding'] = temp_shareholding_data['participant_pct_holding'].str.slice(start = 57)
            temp_shareholding_data['date']                    = d
            
            # Extract total issue
            total_issue = float(self.driver.find_element(By.XPATH, "//div[contains(@class,'summary-value')]").text.replace(',',''))
            
            # Re-calculate % Holding as WebPage data has less precision
            temp_shareholding_data['participant_pct_holding'] = temp_shareholding_data['participant_shares'] / total_issue
            
            # Concatenate data as of t to overall DataFrame
            shareholding_data = pd.concat([shareholding_data, temp_shareholding_data], ignore_index = True)
        
        # Create time-series of shareholding data
        shareholding_ts = shareholding_data.pivot(index   = ['participant_id', 'participant_name'],
                                                  columns = 'date',
                                                  values  = 'participant_pct_holding').T

        del shareholding_data
        
        # Calculate difference in % holdings and create summary DataFrame
        shareholding_ts = shareholding_ts.fillna(0)

        shareholding_ts.index = pd.to_datetime(shareholding_ts.index)
        shareholding_ts = shareholding_ts.diff()
        shareholding_ts = shareholding_ts.fillna(0)

        shareholding_ts[(shareholding_ts < self.user_input.chg_threshold) & (shareholding_ts > -self.user_input.chg_threshold)] = 0

        shareholding_ts = shareholding_ts.loc[:, (shareholding_ts != 0).any(axis=0)]
        shareholding_ts = shareholding_ts.loc[(shareholding_ts != 0).any(axis=1)]

        if len(shareholding_ts.columns) == 0:

            print('No shareholders have shifted their % shareholding by more than or equal to +-' +
                  str(self.user_input.chg_threshold * 100) +
                  '% between ' +
                  self.user_input.start_date +
                  ' and ' +
                  self.user_input.end_date + '.'
                  )

            self.chg_summary = None

        else:
            chg_summary = pd.DataFrame(columns = ['Participant ID',
                                                  'Name of CCASS Participant',
                                                  '% Change in total number of Issued Shares/ Warrants/ Units held',
                                                  'Date of Transaction'
                                                  ])

            for d in shareholding_ts.index:
                temp_data = shareholding_ts.loc[d, :].to_frame()
                temp_data = temp_data[temp_data[d]!=0]
                temp_data = temp_data.reset_index()
                temp_data = temp_data.rename(columns = {'participant_id': 'Participant ID',
                                                        'participant_name': 'Name of CCASS Participant',
                                                        d: '% Change in total number of Issued Shares/ Warrants/ Units held'})
                temp_data['Date of Transaction'] = d

                chg_summary = pd.concat([chg_summary, temp_data], ignore_index = True)

            self.chg_summary = chg_summary
