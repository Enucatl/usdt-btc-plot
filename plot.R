#!/usr/bin/env Rscript

library(argparse)
library(ggplot2)
library(data.table)
library(anytime)
library(scales)
library(zoo)

commandline_parser = ArgumentParser(description="plot usdt data")
commandline_parser$add_argument("usdt", nargs="?", default="usdt.csv")
commandline_parser$add_argument("btc", nargs="?", default="btc.csv")
args = commandline_parser$parse_args()

usdt = fread(args$usdt)
usdt[, date := anytime(blocktime)]
btc = fread(args$btc)
btc[, date := anytime(Timestamp)]
merged = merge(usdt, btc, by="date", all=TRUE, sort=TRUE)
setorder(usdt, "date")
filled = na.locf(merged[, Vwap.BTCUSD])
merged[, filledvwap := filled]
filledvwap = merged[!is.na(amount), filledvwap]
usdt[, filledvwap := filledvwap]
print(usdt)

start_date = "2017-01-01"
plot = ggplot(btc[date > start_date,]) +
    geom_line(aes(x=date, y=Vwap.BTCUSD)) +
    geom_point(data=usdt[date > start_date, ], aes(x=date, y=filledvwap, size=amount), colour="red") +
    scale_size_area(breaks=c(1e7, 2e7, 3e7), labels=c("10M", "20M", "30M"), name="generated\nUSDT") +
    scale_x_datetime() +
    xlab("date") +
    ylab("BTC hourly vwap")
print(plot)
width = 10
factor = 0.618
height = factor * width
ggsave("plot.png", plot, width=width, height=height, dpi=300)
invisible(readLines("stdin", n=1))
