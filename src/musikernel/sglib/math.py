from math import log, pow
from pymarshal import pm_assert
import math


__all__ = [
    'clip_max',
    'clip_min',
    'clip_value',
    'cosine_interpolate',
    'db_to_lin',
    'hz_to_pitch',
    'lin_to_db',
    'linear_interpolate',
    'pan_stereo',
    'pitch_to_hz',
    'pitch_to_ratio',
    'ratio_to_pitch',
]

def pitch_to_hz(pitch):
    return (440.0 * pow(2.0, (float(pitch) - 57.0) * 0.0833333))

def hz_to_pitch(hz):
    return ((12.0 * log(float(hz) * (1.0 / 440.0), 2.0)) + 57.0)

def pitch_to_ratio(pitch):
    return (1.0 / pitch_to_hz(0.0)) * pitch_to_hz(float(pitch))

def ratio_to_pitch(ratio):
    base = (pitch_to_hz(0.0))
    hz = base * ratio
    return hz_to_pitch(hz)

def db_to_lin(value):
    return pow(10.0, (0.05 * float(value)))

def lin_to_db(value):
    if value >= 0.001:
        return log(float(value), 10.0) * 20.0
    else:
        return -120.0

def linear_interpolate(point1, point2, frac):
    return ((1.0 - frac) * point1) + (frac * point2)

def cosine_interpolate(y1, y2, mu):
   mu2 = (1.0 - math.cos(mu * math.pi)) / 2
   return(y1 * (1.0 - mu2) + y2 * mu2)

def clip_value(
    val,
    _min,
    _max,
    _round=False,
):
    if val < _min:
        result = _min
    elif val > _max:
        result =  _max
    else:
        result = val
    if _round:
        result = round(result, 6)
    return result

def clip_min(val, _min):
    if val < _min:
        return _min
    else:
        return val

def clip_max(val, _max):
    if val > _max:
        return _max
    else:
        return val

def pan_stereo(
    pan,
    pan_law,
    volume,
):
    """ Calculate left and right channel volume
        @pan:
            float or tuple, The amount of pan -1 to 1.
            If a tuple, values should be in order of precedence first.  The
            first non-None value will be selected.
        @pan_law:
            float, The amount of pan law.  Normal values
            will be 0., -3., or -4.5.
        @volume:
            float, The combined volume of the item reference, in decibels.
            Should be the sum of all volume parameters.

        @return:
            (float, float), The left and right channel, linear (not decibels)
        @raises:
            ValueError: If @pan is outside the range of -1. to 1.
    """
    if isinstance(pan, tuple):
        if all(x is None for x in pan):
            return (
                db_to_lin(volume),
            ) * 2
        else:
            pan = [x for x in pan if x is not None][0]
    pm_assert(
        pan >= -1. and pan <= 1.,
        ValueError,
        pan,
    )
    if pan == 0.:
        return (
            db_to_lin(volume),
        ) * 2
    elif pan < 0.:  # left
        left = pan * pan_law
        right = pan * 24.
        return (
            db_to_lin(left + volume),
            db_to_lin(right + volume),
        )
    else:  # > 0. , right
        left = pan * -24.
        right = pan * pan_law * -1.
        return (
            db_to_lin(left + volume),
            db_to_lin(right + volume),
        )

