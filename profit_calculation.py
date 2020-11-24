import signal
import sys
import requests
import datetime
from bs4 import BeautifulSoup
from os import path
import re
import pprint
import json
import argparse
import matplotlib.pyplot as plt

# curl example
#  ============================
#  curl 'https://www.spensiones.cl/apps/rentabilidad/getRentabilidad.php?tiprent=FP&template=0' -H 'Content-Type: application/x-www-form-urlencoded' --data-raw 'aaaa=2005&mm=08&btn=Buscar'
#  ============================

# Parameters and basic config
#  ============================
VERSION = "0.0.2"
FUND_DATA = 'fund_data.json'
FUND_SEPARATED_DATA = 'fund_separated_data.json'
pp = pprint.PrettyPrinter(indent=2)
#  ============================

# Ctrl + C Handler
#  ============================
def signal_handler(sig, frame):
    print('Cerrando program')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
#  ============================

def main():  
  # Parser
  # ============================
  parser = argparse.ArgumentParser(description='Script para calcular y entender un poco las pensiones y rentabiliades, a partir de los datos obtenidos de la superintendencia de pensiones')
  parser.add_argument('--afp', help='AFP de la cual se obtendrán los datos.', default='cuprum', action="store", dest="afp", required=False)
  parser.add_argument('-i','--income', help='Ingreso bruto.', default=1000000, action="store", dest="income", required=False)
  parser.add_argument('-c','--commission', help='Comision de la AFP.', default=1.44, action="store",dest="commission", required=False)  
  parser.add_argument('-f','--fondo', help='Fondo a revisar.', default='A', action="store",dest="fund", required=False)  
  parser.add_argument('-a','--action',help='Acción a realizar', default='plot_fund', choices=['get_data', 'plot_fund', 'plot_funds'], action="store",dest="action", required=False)
  parser.add_argument('--version', action='version', version='%(prog)s  v'+VERSION, help="Muestra la versión del programa")
  
  args = parser.parse_args()

  afp = args.afp
  full_income = args.income
  fund = args.fund
  afp_commission = args.commission
  afp_amount = 10.0
  action = args.action
  # ============================  

  print('''
  Parámetros a utilizar
  AFP: %s
  Ingreso Bruto: $%s
  Fondo: %s
  Comisión AFP: %.2f
  Porcentaje destinado a pensión: %.2f
  Acción: %s'''%(afp, "${:,.0f}".format(float(full_income)).replace(',','.'),fund, afp_commission, afp_amount, action))

  # Action to do
  # ============================
  if action == 'get_data':
    get_data(afp)
  elif action == 'plot_fund':
    fund_data, fund_separated_data = load_data()  
    plot_fund(fund, full_income, afp_commission, afp_amount, fund_separated_data)
  elif action == 'plot_funds':
    plot_data(fund_separated_data)
  # ============================

  exit()


# Plots data of an specific fund, considering an income
# ============================
def plot_fund(fund, full_income, afp_commission, afp_amount, data):
  afp_amount_exact = afp_amount*(full_income/100)

  total_data = []
  your_data = []
  # Calculate cumulative profit of your money
  for index, profit in enumerate(data[fund]):
    if index == 0:
      total_data.append((profit/100+1)*afp_amount_exact)
      your_data.append(afp_amount_exact)
    else:
      total_data.append((profit/100+1)*(afp_amount_exact+total_data[index-1]))
      your_data.append(afp_amount_exact+your_data[index-1])

  print('''  Rentabilidad del periodo: %.2f''' %((total_data[-1]/your_data[-1])-1.0))
  plt.plot(total_data)
  plt.plot(your_data)  
  plt.show()
    
# ============================

# Plot cumulative monthly-profit data of all funds
#  ============================
def plot_data(data):
  for fund in ['A', 'B', 'C', 'D', 'E']:
    cumulative = []
    for index, point in enumerate(data[fund]):
      if index == 0:
        cumulative.append(point)
      else:
        cumulative.append(cumulative[index - 1]+point)
    plt.plot(cumulative)
  plt.show()
#  ============================

# Loads data from files
#  ============================
def load_data():
  if not path.exists(FUND_DATA) and not path.exists(FUND_SEPARATED_DATA):
    print("No se encontraron los archivos '%s' y '%s'" %(FUND_DATA, FUND_SEPARATED_DATA))
    exit(1)

  with open(FUND_DATA, 'r') as f:       
    fund_data = json.load(f) 
  with open(FUND_SEPARATED_DATA, 'r') as f:       
    fund_separated_data = json.load(f) 
  
  return fund_data, fund_separated_data
#  ============================

# Retrieve data from spensiones and save it to files
#  ============================
def get_data(afp_name):
  init_month = 8
  init_year = 2005
  end_year = datetime.datetime.now().year
  end_month = datetime.datetime.now().month

  if end_month == 1:
    end_month = 12
    end_year = end_year - 1
  else:
    end_month = end_month - 1 

  dif = date_diff(init_year, init_month, end_year, end_month)
  
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
          if td.contents[0].lower() == afp_name.lower():
            profit_value = tds[index+1].contents[0]
            fund_data[date_index][fund] = profit_value
            if fund not in fund_separated_data:
              fund_separated_data[fund] = []            
            fund_separated_data[fund].append(float(profit_value.replace('%','').replace(',','.')))
            break
     
    if year == end_year and month == end_month:
      break
    else:
      month = month + 1
      if month == 13:
        month = 1
        year = year + 1
      

  with open(FUND_DATA, 'w') as f:
    json.dump(fund_data, f)
  with open(FUND_SEPARATED_DATA, 'w') as f:
    json.dump(fund_separated_data, f)
#  ============================

def date_diff(init_year, init_month, end_year, end_month):
  counter = 0
  month = init_month
  year = init_year
  while(1):
    if year == end_year and month == end_month:
      break
    else:
      counter = counter + 1
      month = month + 1
      if month == 13:
        month = 1
        year = year + 1      
  return counter

if __name__ == "__main__":  
  main()
  # get_data()
  # plot_data()