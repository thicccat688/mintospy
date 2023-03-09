from mintospy.api import MintosApi
from mintospy.enums import Currency
from mintospy.utils import Utils
import pandas as pd
import os


email = os.getenv(key='email')
password = os.getenv(key='password')
tfa_secret = os.getenv(key='tfa_secret')


mintos_client = MintosApi(
    email=email,
    password=password,
    tfa_secret=tfa_secret,
)

kzt_investments = mintos_client.get_investments(currency=Currency.KZT, quantity=1000, current=False)
eur_investments = mintos_client.get_investments(currency=Currency.EUR, quantity=1000, current=False)

schedules = []

for isin in [*eur_investments.index, *kzt_investments.index]:
    schedules.append(mintos_client.get_note_schedule(isin, raw=True))

df_parsed_response = list(map(lambda item: Utils.parse_note_schedule(item[0]), schedules))

schedule_df = pd.DataFrame(df_parsed_response).set_index('identifier').fillna('N/A')

schedule_df.to_csv('sample_loans.csv')
