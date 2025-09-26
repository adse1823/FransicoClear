import pandas as pd

df = pd.read_csv('edges.csv')


df1 = df[['u','v']]

df1.to_csv('edd.csv',index=False)