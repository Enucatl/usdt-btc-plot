# get data

```
wget https://www.bfxdata.com/csv/vwapHourlyBTCUSD.csv
sed 's/"Vwap (BTCUSD)"/Vwap.BTCUSD/' vwapHourlyBTCUSD.csv > data/btc.csv
python tokencreation.py data/usdt.csv
```

# plot
```
./plot.R data/usdt.csv data/btc.csv
```
