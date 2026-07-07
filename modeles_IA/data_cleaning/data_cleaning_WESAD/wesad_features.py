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


#------------------filrage---------------------------------------------------
def _bandpass(sig,fs,low,high,order = 3):
    nyq = 0.5 *fs # frequence de nyquist
    #normalisation des frequence 
    low = low / nyq
    high = min(high/nyq,0.99)
    b, a = butter(order,[low, high], btype="band")
    return filtfilt(b, a, sig)

#-----------------------detection des pincs--------------------------------
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
