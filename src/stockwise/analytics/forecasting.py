"""
Análisis de series temporales y pronóstico de precios (ARIMA / ETS / Theta / Ensamble)
con backtest y simulación Monte Carlo.

Metodología:
  - Se modela el log-precio de cierre (los intervalos de confianza quedan siempre positivos
    y los retornos son aproximadamente aditivos).
  - Modelos candidatos:
      * ARIMA (orden elegido por AIC con d determinado por test ADF).
      * ETS (error aditivo, tendencia aditiva amortiguada).
      * Theta Model (descomposición en curvatura y tendencia, ganador histórico M3).
      * Ensamble (combinación ponderada inversamente por el MAE del backtest).
  - Simulación Monte Carlo (GBM): genera abanicos de probabilidad (Fan Charts),
    probabilidad de ganancia/pérdida y probabilidad de toque de soporte y resistencia.
  - Backtest 'hold-out': se ajusta con los datos menos las últimas `h` ruedas, se pronostica
    esa ventana y se compara contra la realidad y contra el benchmark ingenuo (random walk).
  - Con modelo 'auto' se elige el de menor error en el backtest entre todos los candidatos.

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
from statsmodels.tsa.forecasting.theta import ThetaModel
from statsmodels.tsa.stattools import adfuller

from stockwise.analytics.monte_carlo import simulate_monte_carlo

BASE_MODELS = ("arima", "ets", "theta")
MODELS = ("auto", "arima", "ets", "theta", "ensemble")
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
        if self.kind == "theta":
            fc = self.result.forecast(steps)
            pi = self.result.prediction_intervals(steps=steps, alpha=alpha)
            return pd.DataFrame({
                "mean": np.asarray(fc),
                "lower": np.asarray(pi["lower"]),
                "upper": np.asarray(pi["upper"]),
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


def _fit_theta(log_close: pd.Series) -> _Fit:
    """Theta Model (M3): descompone en curvas de tendencia y curvatura."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = ThetaModel(pd.Series(log_close.values), deseasonalize=False).fit()
    return _Fit("theta", "Theta Model (desestacionalizado=False)", res, "theta", None)


_FITTERS = {"arima": _fit_arima, "ets": _fit_ets, "theta": _fit_theta}


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
        "_last_train": last_train,
    }


def _combine_backtests(base_bts: dict[str, dict[str, Any]], holdout: int) -> dict[str, Any]:
    """Combina los backtests de los modelos base usando promedio de pronósticos y bandas."""
    models = list(base_bts.keys())
    actual = base_bts[models[0]]["_actual"]
    test_dates = base_bts[models[0]]["_dates"]
    naive_mae = base_bts[models[0]]["naive_mae"]
    last_train = base_bts[models[0]]["_last_train"]

    pred_ens = np.mean([base_bts[m]["_pred"] for m in models], axis=0)
    lower_ens = np.mean([base_bts[m]["_lower"] for m in models], axis=0)
    upper_ens = np.mean([base_bts[m]["_upper"] for m in models], axis=0)

    mae_ens = float(np.mean(np.abs(actual - pred_ens)))
    mape_ens = float(np.mean(np.abs((actual - pred_ens) / actual)) * 100)
    rmse_ens = float(np.sqrt(np.mean((actual - pred_ens) ** 2)))
    skill_ens = round((1 - mae_ens / naive_mae) * 100, 2) if naive_mae else None
    direction_ok = bool(np.sign(pred_ens[-1] - last_train) == np.sign(actual[-1] - last_train))
    ci_cov = round(float(np.mean((actual >= lower_ens) & (actual <= upper_ens)) * 100), 1)

    return {
        "model": f"Ensamble ({' + '.join(models)})",
        "holdout_days": int(holdout),
        "mae": round(mae_ens, 4),
        "mape_pct": round(mape_ens, 2),
        "rmse": round(rmse_ens, 4),
        "naive_mae": round(naive_mae, 4),
        "skill_vs_naive_pct": skill_ens,
        "direction_correct": direction_ok,
        "ci_coverage_pct": ci_cov,
        "_dates": test_dates,
        "_pred": pred_ens,
        "_lower": lower_ens,
        "_upper": upper_ens,
        "_actual": actual,
        "_last_train": last_train,
    }


def _public(bt: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in bt.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# API principal
# ---------------------------------------------------------------------------
def forecast_close(
    df: pd.DataFrame,
    horizon: int = 30,
    model: str = "auto",
    support_price: float | None = None,
    resistance_price: float | None = None,
    n_simulations: int = 2000,
) -> dict[str, Any]:
    """
    Pronostica el precio de cierre `horizon` ruedas hacia adelante con modelos de series de tiempo
    (ARIMA, ETS, Theta, Ensamble) y complementa con simulación Monte Carlo (GBM).

    Devuelve un dict con:
      - 'series': Serie de cierres usada (pd.Series, para graficar).
      - 'forecast': DataFrame (index=fechas futuras; columnas mean, lower, upper en precio).
      - 'backtest': dict con métricas y datos de la ventana de validación.
      - 'monte_carlo': dict con métricas de simulación y DataFrame fan_chart.
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

    # Determinar qué modelos base evaluar en el backtest
    if model in BASE_MODELS:
        candidates = [model]
    else:
        candidates = list(BASE_MODELS)

    backtests: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    for m in candidates:
        try:
            backtests[m] = _backtest(log_close, m, holdout)
        except Exception as exc:  # un modelo fallido no debe tumbar al resto
            errors[m] = str(exc)

    if not backtests:
        raise RuntimeError(f"No fue posible ajustar los modelos solicitados: {errors}")

    # Si se solicitó auto o ensemble, agregamos el ensamble si hay al menos 2 modelos base válidos
    if model in ("auto", "ensemble") and len(backtests) >= 2:
        backtests["ensemble"] = _combine_backtests(backtests, holdout)

    if model == "ensemble":
        if "ensemble" not in backtests:
            raise RuntimeError(f"No fue posible construir el ensamble: {errors}")
        chosen = "ensemble"
    elif model == "auto":
        chosen = min(backtests, key=lambda m: backtests[m]["mae"])
    else:
        chosen = model

    dates = future_business_days(close.index[-1], horizon)
    ljung_p: float | None = None
    ensemble_weights: dict[str, float] | None = None

    if chosen == "ensemble":
        # Ajuste de cada modelo base sobre la serie completa y ponderación por inversa de MAE
        base_models_fitted = {}
        for m in BASE_MODELS:
            if m in backtests:
                try:
                    base_models_fitted[m] = _FITTERS[m](log_close)
                except Exception:
                    pass

        if not base_models_fitted:
            raise RuntimeError("No fue posible ajustar los modelos base para el ensamble.")

        base_fcs = {m: fit.forecast(horizon) for m, fit in base_models_fitted.items()}
        inv_maes = {m: 1.0 / max(float(backtests[m]["mae"]), 1e-6) for m in base_fcs}
        tot_inv = sum(inv_maes.values())
        weights = {m: inv_maes[m] / tot_inv for m in inv_maes}
        ensemble_weights = {m: round(float(w), 4) for m, w in weights.items()}

        mean_future = sum(weights[m] * np.exp(base_fcs[m]["mean"].values) for m in base_fcs)
        lower_future = sum(weights[m] * np.exp(base_fcs[m]["lower"].values) for m in base_fcs)
        upper_future = sum(weights[m] * np.exp(base_fcs[m]["upper"].values) for m in base_fcs)

        forecast = pd.DataFrame(
            {"mean": mean_future, "lower": lower_future, "upper": upper_future},
            index=dates,
        )
        w_text = ", ".join(f"{m}:{w:.0%}" for m, w in weights.items())
        model_desc = f"Ensamble ponderado ({w_text})"
    else:
        final = _FITTERS[chosen](log_close)
        fc = final.forecast(horizon)
        forecast = pd.DataFrame(
            {"mean": np.exp(fc["mean"].values), "lower": np.exp(fc["lower"].values), "upper": np.exp(fc["upper"].values)},
            index=dates,
        )
        model_desc = final.description

        # Diagnóstico de residuos (Ljung-Box): ¿queda autocorrelación sin explicar?
        resid = getattr(final.result, "resid", None)
        if resid is not None:
            try:
                resid_arr = np.asarray(resid)[-min(len(close), 250):]
                lb = acorr_ljungbox(resid_arr, lags=[10], return_df=True)
                ljung_p = round(float(lb["lb_pvalue"].iloc[0]), 4)
            except Exception:
                pass

    # Simulación Monte Carlo complementaria
    mc = simulate_monte_carlo(
        close,
        horizon=horizon,
        n_simulations=n_simulations,
        support_price=support_price,
        resistance_price=resistance_price,
    )

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
        "model_selected": model_desc,
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
        "ensemble_weights": ensemble_weights,
        "monte_carlo": mc["summary"],
        "residuals_ljung_box_p": ljung_p,
        "model_errors": errors or None,
        "warnings": warn,
    }
    return {
        "series": close,
        "forecast": forecast,
        "backtest": bt,
        "monte_carlo": mc,
        "summary": summary,
    }
