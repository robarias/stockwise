"""
Análisis de series temporales y pronóstico de precios (ARIMA / ETS) con backtest.

Metodología:
  - Se modela el log-precio de cierre (los intervalos de confianza quedan siempre positivos
    y los retornos son aproximadamente aditivos).
  - Modelos candidatos: ARIMA (orden elegido por AIC) y ETS (tendencia aditiva amortiguada).
  - Backtest 'hold-out': se ajusta con los datos menos las últimas `h` ruedas, se pronostica
    esa ventana y se compara contra la realidad y contra el benchmark ingenuo (random walk).
  - Con modelo 'auto' se elige el de menor error en el backtest.

Advertencia: los precios bursátiles son casi un paseo aleatorio; un pronóstico estadístico
rara vez supera al benchmark ingenuo. Las métricas de backtest se reportan para evidenciarlo.
"""

import itertools
import warnings
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.stattools import adfuller

MODELS = ("auto", "arima", "ets")
MIN_OBSERVATIONS = 60
CONFIDENCE = 0.95


# ---------------------------------------------------------------------------
# Preparación
# ---------------------------------------------------------------------------
def prepare_close_series(df: pd.DataFrame) -> pd.Series:
    """Serie de cierres limpia: sin NaN, índice sin zona horaria, ordenado y sin duplicados."""
    if "Close" not in df.columns:
        raise ValueError("El DataFrame debe contener la columna 'Close'.")
    s = df["Close"].astype(float).dropna()
    s = s[s > 0]
    if isinstance(s.index, pd.DatetimeIndex) and s.index.tz is not None:
        s.index = s.index.tz_localize(None)
    s.index = pd.DatetimeIndex(s.index).normalize()
    s = s[~s.index.duplicated(keep="last")].sort_index()
    if len(s) < MIN_OBSERVATIONS:
        raise ValueError(
            f"Se requieren al menos {MIN_OBSERVATIONS} observaciones; hay {len(s)}. Use un periodo más largo."
        )
    return s


def future_business_days(last_date: pd.Timestamp, horizon: int) -> pd.DatetimeIndex:
    """Próximas `horizon` ruedas (lunes a viernes; no considera festivos bursátiles)."""
    return pd.bdate_range(start=last_date + pd.Timedelta(days=1), periods=horizon)


# ---------------------------------------------------------------------------
# Diagnósticos
# ---------------------------------------------------------------------------
def adf_test(series: pd.Series) -> dict[str, Any]:
    """Prueba Dickey-Fuller aumentada. H0: la serie tiene raíz unitaria (no estacionaria)."""
    stat, pvalue, usedlag, nobs, crit, _ = adfuller(series.values, autolag="AIC", result_object=False)
    return {
        "statistic": round(float(stat), 4),
        "p_value": round(float(pvalue), 4),
        "critical_values": {k: round(float(v), 4) for k, v in crit.items()},
        "stationary": bool(pvalue < 0.05),
    }


# ---------------------------------------------------------------------------
# Ajuste de modelos (sobre log-precio)
# ---------------------------------------------------------------------------
class _Fit:
    """Resultado de ajustar un modelo: pronostica media y bandas en log-precio."""

    def __init__(self, name: str, description: str, result: Any, kind: str, aic: float | None):
        self.name, self.description, self.result, self.kind, self.aic = name, description, result, kind, aic

    def forecast(self, steps: int, alpha: float = 1 - CONFIDENCE) -> pd.DataFrame:
        """DataFrame con columnas mean, lower, upper (en escala log) indexado 0..steps-1."""
        if self.kind == "arima":
            fc = self.result.get_forecast(steps=steps)
            ci = fc.conf_int(alpha=alpha)
            return pd.DataFrame({
                "mean": np.asarray(fc.predicted_mean),
                "lower": np.asarray(ci)[:, 0],
                "upper": np.asarray(ci)[:, 1],
            })
        pred = self.result.get_prediction(start=self.result.nobs, end=self.result.nobs + steps - 1)
        frame = pred.summary_frame(alpha=alpha)
        return pd.DataFrame({
            "mean": frame["mean"].values,
            "lower": frame["pi_lower"].values,
            "upper": frame["pi_upper"].values,
        })


def _fit_arima(log_close: pd.Series) -> _Fit:
    """ARIMA con d decidido por ADF y (p, q, tendencia) elegidos por menor AIC."""
    d = 0 if adf_test(log_close)["stationary"] else 1
    trends = ["c", "n"] if d == 0 else ["t", "n"]
    y = log_close.values
    best: tuple[float, tuple[int, int, int], str, Any] | None = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for p, q, trend in itertools.product(range(3), range(3), trends):
            if p == 0 and q == 0 and d == 0 and trend == "n":
                continue
            try:
                res = ARIMA(y, order=(p, d, q), trend=trend).fit()
            except Exception:
                continue
            if not np.isfinite(res.aic):
                continue
            if best is None or res.aic < best[0]:
                best = (res.aic, (p, d, q), trend, res)
    if best is None:
        raise RuntimeError("No fue posible ajustar ningún modelo ARIMA.")
    aic, order, trend, res = best
    return _Fit("arima", f"ARIMA{order} trend='{trend}'", res, "arima", float(aic))


def _fit_ets(log_close: pd.Series) -> _Fit:
    """ETS: error aditivo, tendencia aditiva amortiguada, sin estacionalidad."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = ETSModel(pd.Series(log_close.values), error="add", trend="add", damped_trend=True).fit(disp=False)
    return _Fit("ets", "ETS(A,Ad,N) tendencia aditiva amortiguada", res, "ets", float(res.aic))


_FITTERS = {"arima": _fit_arima, "ets": _fit_ets}


# ---------------------------------------------------------------------------
# Backtest
# ---------------------------------------------------------------------------
def _backtest(log_close: pd.Series, model: str, holdout: int) -> dict[str, Any]:
    """Ajusta con datos[:-holdout], pronostica `holdout` pasos y mide el error vs lo ocurrido."""
    train, test = log_close.iloc[:-holdout], log_close.iloc[-holdout:]
    fit = _FITTERS[model](train)
    fc = fit.forecast(holdout)

    actual = np.exp(test.values)
    pred = np.exp(fc["mean"].values)
    naive = np.full_like(actual, float(np.exp(train.iloc[-1])))
    lower, upper = np.exp(fc["lower"].values), np.exp(fc["upper"].values)

    mae, mae_naive = float(np.mean(np.abs(actual - pred))), float(np.mean(np.abs(actual - naive)))
    last_train = float(np.exp(train.iloc[-1]))
    direction_ok = bool(np.sign(pred[-1] - last_train) == np.sign(actual[-1] - last_train))

    return {
        "model": fit.description,
        "holdout_days": int(holdout),
        "mae": round(mae, 4),
        "mape_pct": round(float(np.mean(np.abs((actual - pred) / actual)) * 100), 2),
        "rmse": round(float(np.sqrt(np.mean((actual - pred) ** 2))), 4),
        "naive_mae": round(mae_naive, 4),
        "skill_vs_naive_pct": round((1 - mae / mae_naive) * 100, 2) if mae_naive else None,
        "direction_correct": direction_ok,
        "ci_coverage_pct": round(float(np.mean((actual >= lower) & (actual <= upper)) * 100), 1),
        "_dates": test.index,
        "_pred": pred,
        "_lower": lower,
        "_upper": upper,
        "_actual": actual,
    }


def _public(bt: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in bt.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# API principal
# ---------------------------------------------------------------------------
def forecast_close(df: pd.DataFrame, horizon: int = 30, model: str = "auto") -> dict[str, Any]:
    """
    Pronostica el precio de cierre `horizon` ruedas hacia adelante.

    Devuelve un dict con:
      - 'series': Serie de cierres usada (pd.Series, para graficar).
      - 'forecast': DataFrame (index=fechas futuras; columnas mean, lower, upper en precio).
      - 'backtest': dict con métricas y, en claves '_*', los datos para graficar.
      - 'summary': resumen serializable (JSON).
    """
    model = model.lower().strip()
    if model not in MODELS:
        raise ValueError(f"Modelo '{model}' no soportado. Opciones: {', '.join(MODELS)}.")
    if not 1 <= horizon <= 252:
        raise ValueError("`horizon` debe estar entre 1 y 252 ruedas.")

    close = prepare_close_series(df)
    log_close = np.log(close)

    holdout = int(min(max(horizon, 10), 60, len(close) // 4))
    candidates = list(_FITTERS) if model == "auto" else [model]
    backtests, errors = {}, {}
    for m in candidates:
        try:
            backtests[m] = _backtest(log_close, m, holdout)
        except Exception as exc:  # un modelo fallido no debe tumbar al resto
            errors[m] = str(exc)
    if not backtests:
        raise RuntimeError(f"No fue posible ajustar los modelos solicitados: {errors}")

    chosen = min(backtests, key=lambda m: backtests[m]["mae"])
    final = _FITTERS[chosen](log_close)
    fc = final.forecast(horizon)
    dates = future_business_days(close.index[-1], horizon)
    forecast = pd.DataFrame(
        {"mean": np.exp(fc["mean"].values), "lower": np.exp(fc["lower"].values), "upper": np.exp(fc["upper"].values)},
        index=dates,
    )

    # Diagnóstico de residuos (Ljung-Box): ¿queda autocorrelación sin explicar?
    ljung_p = None
    try:
        resid = np.asarray(final.result.resid)[-min(len(close), 250):]
        lb = acorr_ljungbox(resid, lags=[10], return_df=True)
        ljung_p = round(float(lb["lb_pvalue"].iloc[0]), 4)
    except Exception:
        pass

    last_price = float(close.iloc[-1])
    end_mean = float(forecast["mean"].iloc[-1])
    bt = backtests[chosen]
    warn = []
    if bt["skill_vs_naive_pct"] is not None and bt["skill_vs_naive_pct"] <= 0:
        warn.append("En el backtest el modelo NO superó al benchmark ingenuo (precio constante): "
                    "trate el pronóstico con escepticismo.")
    if bt["ci_coverage_pct"] < 80:
        warn.append("El intervalo de confianza cubrió menos del 80% de los precios reales en el backtest "
                    "(el modelo subestima la incertidumbre).")
    if ljung_p is not None and ljung_p < 0.05:
        warn.append("Los residuos muestran autocorrelación (Ljung-Box p<0.05): el modelo no captura toda la dinámica.")
    warn.append("Los precios bursátiles se comportan casi como un paseo aleatorio; esto no es una recomendación de inversión.")

    summary = {
        "model_selected": final.description,
        "selection": "auto (menor MAE en backtest)" if model == "auto" else "manual",
        "observations": int(len(close)),
        "history_range": [close.index[0].strftime("%Y-%m-%d"), close.index[-1].strftime("%Y-%m-%d")],
        "stationarity_log_price": adf_test(log_close),
        "last_price": round(last_price, 2),
        "horizon_days": int(horizon),
        "forecast_end_date": dates[-1].strftime("%Y-%m-%d"),
        "forecast_end": {
            "mean": round(end_mean, 2),
            "lower_95": round(float(forecast["lower"].iloc[-1]), 2),
            "upper_95": round(float(forecast["upper"].iloc[-1]), 2),
            "expected_change_pct": round((end_mean / last_price - 1) * 100, 2),
        },
        "backtest": _public(bt),
        "backtest_all_models": {m: _public(b) for m, b in backtests.items()} if len(backtests) > 1 else None,
        "residuals_ljung_box_p": ljung_p,
        "model_errors": errors or None,
        "warnings": warn,
    }
    return {"series": close, "forecast": forecast, "backtest": bt, "summary": summary}
