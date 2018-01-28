#!/usr/bin/env Rscript

library(argparse)
library(ggplot2)
library(data.table)
library(anytime)
library(scales)
library(zoo)

commandline_parser = ArgumentParser(description="plot usdt data")
commandline_parser$add_argument("usdt", nargs="?", default="data/usdt.csv")
commandline_parser$add_argument("btc", nargs="?", default="data/btc.csv")
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
print(btc)

start_date = "2017-06-01"
plot = ggplot(btc[date > start_date,]) +
    geom_line(aes(x=date, y=Vwap.BTCUSD)) +
    geom_point(data=usdt[date > start_date, ], aes(x=date, y=filledvwap, size=amount), colour="red") +
    scale_size_area(breaks=c(1e7, 5e7, 10e7), labels=c("10M", "50M", "100M"), name="generated\nUSDT") +
    scale_x_datetime(labels=date_format("%m/%Y")) +
    theme(axis.text.x=element_text(angle=60, hjust=1)) +
    xlab("date") +
    ylab("BTC hourly vwap")

width = 20
factor = 0.618
height = factor * width
print(plot)
ggsave("plot.png", plot, width=width, height=height, dpi=300)
invisible(readLines("stdin", n=1))
