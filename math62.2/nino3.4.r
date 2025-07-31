library('tseries')
library('TSA')
library('forecast')
library('MASS')

# Read CSV
enso = read.csv('C:/Users/Admin/Downloads/test3.1.csv', header=TRUE)
enso

# The dataset consists of two cols. We store each into a unique variable.
p_nino3.4 = ts(enso$nino3.4_sst, start=c(1950,1), frequency=12)

plot(p_nino3.4)

# Test for Stationarity
adf.test(p_nino3.4)

# Test for Autocorrelation
Box.test(p_nino3.4, type='Ljung')

# Remark. nino3.4 are stationary and autocorrelated.

#####
# Correlogram generation
# Note that the lags generated are in terms of years. However, our data is monthly. 
# So we need to find equivalences, to find a lag h (in month) which will be the AR/MA potential order.

# For p_nino3.4,
acf_nino = acf(p_nino3.4, plot=FALSE)
acf_nino$lag = acf_nino$lag * 12
plot(acf_nino, main="ACF for Niño 3.4 index", xlab="Lag (in months)")

pacf_nino = pacf(p_nino3.4, plot=FALSE)
pacf_nino$lag = pacf_nino$lag * 12
plot(pacf_nino, main="PACF for Niño 3.4 index", xlab="Lag (in months)")

# Notes
# ACF --> q = 1, 2, 3
# PACF --> p = 1, 3

stl_nino = decompose(p_nino3.4)
plot(stl_nino)

# Seasonality can be observed. So it might be worthwhile to do differencing.
# For d = 1
nino_d = diff(p_nino3.4, differences=1)
adf.test(nino_d)
Box.test(nino_d, type='Ljung')

acf_nino_d = acf(nino_d, plot=FALSE)
acf_nino_d$lag = acf_nino_d$lag * 12
plot(acf_nino_d, main="ACF for Niño 3.4 index, d=1", xlab="Lag (in months)")

pacf_nino_d = pacf(nino_d, plot=FALSE)
pacf_nino_d$lag = pacf_nino_d$lag * 12
plot(pacf_nino_d, main="ACF for Niño 3.4 index, d=1", xlab="Lag (in months)")

## Seasonality is still observed so we proceed with d=2
# For d = 2
nino_d = diff(p_nino3.4, differences=2)
adf.test(nino_d)
Box.test(nino_d, type='Ljung')

acf_nino_d = acf(nino_d, plot=FALSE)
acf_nino_d$lag = acf_nino_d$lag * 12
plot(acf_nino_d, main="ACF for Niño 3.4 index, d=2", xlab="Lag (in months)")

pacf_nino_d = pacf(nino_d, plot=FALSE)
pacf_nino_d$lag = pacf_nino_d$lag * 12
plot(pacf_nino_d, main="ACF for Niño 3.4 index, d=2", xlab="Lag (in months)")

# ACF --> q = 1, 3
# PACF --> p = 1, 2, 3
# Why cut off until 3? Parsimony

# For nino_diff
nino_ma1 = Arima(nino_d, order=c(0,0,1))
nino_ma3 = Arima(nino_d, order=c(0,0,3))
nino_ar1 = Arima(nino_d, order=c(1,0,0))
nino_ar2 = Arima(nino_d, order=c(2,0,0))
nino_ar3 = Arima(nino_d, order=c(3,0,0))
nino_arma11 = Arima(nino_d, order=c(1,0,1))
nino_arma21 = Arima(nino_d, order=c(2,0,1))
nino_arma31 = Arima(nino_d, order=c(3,0,1))
nino_arma13 = Arima(nino_d, order=c(1,0,3))
nino_arma23 = Arima(nino_d, order=c(2,0,3))
nino_arma33 = Arima(nino_d, order=c(3,0,3))

cbind(nino_ma1$aic, nino_ma3$aic, nino_ar1$aic, nino_ar2$aic, nino_ar3$aic, 
      nino_arma11$aic, nino_arma21$aic, nino_arma31$aic, 
      nino_arma13$aic, nino_arma23$aic, nino_arma33$aic)

nino_arma33


nino_arma33.a = arima(nino_d, order=c(3,0,3))
nino_arma33.a
# Best model is ARMA(3,3)
