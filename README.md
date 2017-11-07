# get data

```
wget https://www.bfxdata.com/csv/vwapHourlyBTCUSD.csv
sed 's/"Vwap (BTCUSD)"/Vwap.BTCUSD/' vwapHourlyBTCUSD.csv > btc.csv
python tokencreation.py usdt.csv btc.csv
```

# plot
```
./plot.R usdt.csv vwapHourlyBTCUSD.csv
```
