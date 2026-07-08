"""
wesad_features.py — Extraction des features physiologiques d'une FENÊTRE de signal.

  ecg_*  : rythme + HRV depuis l'ECG   (AD8232)
  bvp_*  : rythme + variabilité (PPG)  (MAX30102)
  temp_* : statistiques de température
  mot_*  : niveau d'activité / agitation (gyro/ACC)
"""
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks, welch
from scipy.interpolate import interp1d

# np.trapz -> np.trapezoid depuis NumPy 2.0 (compat)
_trapz = getattr(np, "trapezoid", None) or np.trapz


# ---------- Filtrage ----------
def _bandpass(sig, fs, low, high, order=3):
    nyq = 0.5 * fs
    low, high = low / nyq, min(high / nyq, 0.99)
    b, a = butter(order, [low, high], btype="band")
    return filtfilt(b, a, sig)


# ---------- Détection de pics ----------
def rpeaks_ecg(ecg, fs):
    """Pics R (Pan-Tompkins allégé : bande 5-15 Hz -> dérivée -> carré)."""
    filt = _bandpass(ecg, fs, 5, 15)
    squared = np.ediff1d(filt, to_begin=0) ** 2
    dist = int(0.33 * fs)                       # >= 0.33 s => max ~180 bpm
    height = np.mean(squared) + 0.5 * np.std(squared)
    peaks, _ = find_peaks(squared, distance=dist, height=height)
    return peaks


def peaks_ppg(bvp, fs):
    """Pics systoliques du PPG/BVP."""
    filt = _bandpass(bvp, fs, 0.5, 8)
    peaks, _ = find_peaks(filt, distance=int(0.33 * fs),
                          height=np.mean(filt) + 0.3 * np.std(filt))
    return peaks


# ---------- HRV (temporel + fréquentiel) ----------
def hrv_features(peaks, fs, prefix):
    """Features HRV depuis les indices de pics (ECG=RR, PPG=IBI)."""
    f = {}
    keys = ["mean_hr", "mean_rr", "sdnn", "rmssd", "pnn50", "lf_hf"]
    if len(peaks) < 4:
        return {f"{prefix}_{k}": np.nan for k in keys}

    rr = np.diff(peaks) / fs * 1000.0            # RR en ms
    rr = rr[(rr > 300) & (rr < 2000)]            # on jette les RR aberrants
    if len(rr) < 3:
        return {f"{prefix}_{k}": np.nan for k in keys}

    diff_rr = np.diff(rr)
    f[f"{prefix}_mean_hr"] = 60000.0 / np.mean(rr)
    f[f"{prefix}_mean_rr"] = np.mean(rr)
    f[f"{prefix}_sdnn"]    = np.std(rr, ddof=1)            # variabilité globale
    f[f"{prefix}_rmssd"]   = np.sqrt(np.mean(diff_rr ** 2)) # variabilité court-terme
    f[f"{prefix}_pnn50"]   = np.mean(np.abs(diff_rr) > 50) * 100.0
    f[f"{prefix}_lf_hf"]   = _lf_hf_ratio(peaks, fs)
    return f


def _lf_hf_ratio(peaks, fs):
    """Ratio LF/HF (balance sympatho-vagale) via tachogramme rééchantillonné + Welch."""
    try:
        t_peaks = peaks / fs
        rr = np.diff(t_peaks)
        t_rr = t_peaks[1:]
        fs_rr = 4.0
        t_uniform = np.arange(t_rr[0], t_rr[-1], 1 / fs_rr)
        if len(t_uniform) < 8:
            return np.nan
        rr_i = interp1d(t_rr, rr, kind="cubic", fill_value="extrapolate")(t_uniform)
        freqs, psd = welch(rr_i - np.mean(rr_i), fs=fs_rr, nperseg=min(256, len(rr_i)))
        lf = _trapz(psd[(freqs >= 0.04) & (freqs < 0.15)])
        hf = _trapz(psd[(freqs >= 0.15) & (freqs < 0.40)])
        return lf / hf if hf > 0 else np.nan
    except Exception:
        return np.nan


# ---------- Température & mouvement ----------
def temp_features(temp, fs, prefix="temp"):
    f = {f"{prefix}_mean": np.mean(temp), f"{prefix}_std": np.std(temp),
         f"{prefix}_min": np.min(temp),  f"{prefix}_max": np.max(temp),
         f"{prefix}_range": np.max(temp) - np.min(temp)}
    t = np.arange(len(temp)) / fs
    f[f"{prefix}_slope"] = np.polyfit(t, temp, 1)[0] if len(temp) > 2 else np.nan
    return f


def motion_features(mot, fs, prefix="mot"):
    """mot = norme de l'accéléromètre (ou du gyroscope sur ton device)."""
    return {f"{prefix}_mean": np.mean(mot), f"{prefix}_std": np.std(mot),
            f"{prefix}_max": np.max(mot),   f"{prefix}_energy": np.mean(mot ** 2),
            f"{prefix}_jerk": np.mean(np.abs(np.diff(mot)))}


# ---------- Point d'entrée ----------
def extract_window_features(win):
    """win = {'ecg':(sig,fs), 'bvp':(sig,fs), 'temp':(sig,fs), 'motion':(sig,fs)}."""
    feats = {}
    ecg, fs_ecg = win["ecg"]
    feats.update(hrv_features(rpeaks_ecg(ecg, fs_ecg), fs_ecg, prefix="ecg"))
    bvp, fs_bvp = win["bvp"]
    feats.update(hrv_features(peaks_ppg(bvp, fs_bvp), fs_bvp, prefix="bvp"))
    temp, fs_temp = win["temp"]
    feats.update(temp_features(temp, fs_temp))
    mot, fs_mot = win["motion"]
    feats.update(motion_features(mot, fs_mot))
    return feats