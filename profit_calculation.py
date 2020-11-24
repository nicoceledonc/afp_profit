import requests
import datetime
from bs4 import BeautifulSoup
import re
import pprint
import json
import matplotlib.pyplot as plt

pp = pprint.PrettyPrinter(indent=2)

# curl example
#  curl 'https://www.spensiones.cl/apps/rentabilidad/getRentabilidad.php?tiprent=FP&template=0' -H 'Content-Type: application/x-www-form-urlencoded' --data-raw 'aaaa=2005&mm=08&btn=Buscar'

def main():
  afp = 'cuprum'
  full_income = 1000000
  afp_commission = 1.44
  afp_amount = 10.0

  action = 'get_data'

  if action == 'get_data':
    get_data(afp)
  elif action == 'plot_fund':
    fund_data, fund_separated_data = load_data()  
    plot_fund('E', full_income, afp_commission, afp_amount, fund_separated_data)
  elif action == 'plot_funds':
    plot_data(fund_separated_data)

def plot_fund(fund, full_income, afp_commission, afp_amount, data):
  afp_amount_exact = afp_amount*(full_income/100)

  total_data = []
  your_data = []
  for index, profit in enumerate(data[fund]):
    if index == 0:
      total_data.append((profit/100+1)*afp_amount_exact)
      your_data.append(afp_amount_exact)
    else:
      total_data.append((profit/100+1)*(afp_amount_exact+total_data[index-1]))
      your_data.append(afp_amount_exact+your_data[index-1])

  fig, ax = plt.subplots()
  ax.plot(total_data)
  ax.plot(your_data)
  plt.show()
  
  print(total_data[-1]/your_data[-1])

def plot_data(data):
  fig, ax = plt.subplots()
  for fund in ['A', 'B', 'C', 'D', 'E']:
    cumulative = []
    for index, point in enumerate(data[fund]):
      if index == 0:
        cumulative.append(point)
      else:
        cumulative.append(cumulative[index - 1]+point)
    ax.plot(cumulative)
  plt.show()
  
def load_data():
  with open('fund_data.json', 'r') as f:       
    fund_data = json.load(f) 
  with open('fund_separated_data.json', 'r') as f:       
    fund_separated_data = json.load(f) 
  
  return fund_data, fund_separated_data

def get_data(afp_name):

  # Retrieve data from spensiones
  init_month = 8
  init_year = 2005
  end_year = datetime.datetime.now().year
  end_month = datetime.datetime.now().month

  if end_month == 1:
    end_month = 12
    end_year = end_year - 1
  else:
    end_month = end_month - 1 
  
  year = init_year
  month = init_month
  fund_data = {}
  fund_separated_data = {}
  while(1):
    date_index = '%s-%s'%(year,str(month).rjust(2,'0')) 
    fund_data[date_index] = {}
    data = 'aaaa=%s&mm=%s&btn=Buscar' %(year,str(month).rjust(2,'0'))
    headers= {'Content-Type': 'application/x-www-form-urlencoded'}
    url = 'https://www.spensiones.cl/apps/rentabilidad/getRentabilidad.php?tiprent=FP&template=0'
    r = requests.post('https://www.spensiones.cl/apps/rentabilidad/getRentabilidad.php?tiprent=FP&template=0', data=data, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.form.find_all('table')
    
    for table in tables[2:]:
      trs = table.find_all('tr')
      fund = (re.search('TIPO (.) ',str(trs[0])).group(1))      
      for tr in trs[4:]:
        tds = tr.find_all('td')
        for index, td in enumerate(tds):
          if td.contents[0].lower() == apf_name.lower():
            profit_value = tds[index+1].contents[0]
            fund_data[date_index][fund] = profit_value
            if fund not in fund_separated_data:
              fund_separated_data[fund] = []
            try:
              fund_separated_data[fund].append(float(profit_value.replace('%','').replace(',','.')))
            except:
              print(fund)
              print(date_index)
              print(profit_value)
              exit()
            break
     
    if year == end_year and month == end_month:
      break
    else:
      month = month + 1
      if month == 13:
        month = 1
        year = year + 1
      

  # pp.pprint(fund_data)
  # pp.pprint(fund_separated_data)
  with open('fund_data.json', 'w') as f:
    json.dump(fund_data, f)
  with open('fund_separated_data.json', 'w') as f:
    json.dump(fund_separated_data, f)

if __name__ == "__main__":
  main()
  # get_data()
  # plot_data()