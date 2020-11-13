# -*- coding: utf-8 -*-
"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""

from mkpy.libpydaw.pydaw_widgets import *
from mkpy.libpydaw.translate import _
import sys

#Total number of LFOs, ADSRs, other envelopes, etc...
#Used for the PolyFX mod matrix
WAYV_MODULATOR_COUNT = 4
#How many modular PolyFX
WAYV_MODULAR_POLYFX_COUNT = 4
#How many ports per PolyFX, 3 knobs and a combobox
WAYV_PORTS_PER_MOD_EFFECT = 4
#How many knobs per PolyFX, 3 knobs
WAYV_CONTROLS_PER_MOD_EFFECT = 3
WAYV_EFFECTS_GROUPS_COUNT = 1
WAYV_OUTPUT0 = 0
WAYV_OUTPUT1 = 1
WAYV_FIRST_CONTROL_PORT = 2
WAYV_ATTACK_MAIN = 2
WAYV_DECAY_MAIN = 3
WAYV_SUSTAIN_MAIN = 4
WAYV_RELEASE_MAIN = 5
WAYV_NOISE_AMP = 6
WAYV_OSC1_TYPE = 7
WAYV_OSC1_PITCH = 8
WAYV_OSC1_TUNE = 9
WAYV_OSC1_VOLUME = 10
WAYV_OSC2_TYPE = 11
WAYV_OSC2_PITCH = 12
WAYV_OSC2_TUNE = 13
WAYV_OSC2_VOLUME = 14
WAYV_MASTER_VOLUME = 15
WAYV_OSC1_UNISON_VOICES = 16
WAYV_OSC1_UNISON_SPREAD = 17
WAYV_MASTER_GLIDE = 18
WAYV_MASTER_PITCHBEND_AMT = 19
WAYV_ATTACK1 = 20
WAYV_DECAY1 = 21
WAYV_SUSTAIN1 = 22
WAYV_RELEASE1 = 23
WAYV_ATTACK2 = 24
WAYV_DECAY2 = 25
WAYV_SUSTAIN2 = 26
WAYV_RELEASE2 = 27
WAYV_ATTACK_PFX1 = 28
WAYV_DECAY_PFX1 = 29
WAYV_SUSTAIN_PFX1 = 30
WAYV_RELEASE_PFX1 = 31
WAYV_ATTACK_PFX2 = 32
WAYV_DECAY_PFX2 = 33
WAYV_SUSTAIN_PFX2 = 34
WAYV_RELEASE_PFX2 = 35
WAYV_NOISE_TYPE = 36
WAYV_RAMP_ENV_TIME = 37
WAYV_LFO_FREQ = 38
WAYV_LFO_TYPE = 39
WAYV_FX0_KNOB0 = 40
WAYV_FX0_KNOB1 = 41
WAYV_FX0_KNOB2 = 42
WAYV_FX0_COMBOBOX = 43
WAYV_FX1_KNOB0 = 44
WAYV_FX1_KNOB1 = 45
WAYV_FX1_KNOB2 = 46
WAYV_FX1_COMBOBOX = 47
WAYV_FX2_KNOB0 = 48
WAYV_FX2_KNOB1 = 49
WAYV_FX2_KNOB2 = 50
WAYV_FX2_COMBOBOX = 51
WAYV_FX3_KNOB0 = 52
WAYV_FX3_KNOB1 = 53
WAYV_FX3_KNOB2 = 54
WAYV_FX3_COMBOBOX = 55
#PolyFX Mod Matrix
WAVV_PFXMATRIX_FIRST_PORT = 56
WAVV_PFXMATRIX_GRP0DST0SRC0CTRL0 = 56
WAVV_PFXMATRIX_GRP0DST0SRC0CTRL1 = 57
WAVV_PFXMATRIX_GRP0DST0SRC0CTRL2 = 58
WAVV_PFXMATRIX_GRP0DST0SRC1CTRL0 = 59
WAVV_PFXMATRIX_GRP0DST0SRC1CTRL1 = 60
WAVV_PFXMATRIX_GRP0DST0SRC1CTRL2 = 61
WAVV_PFXMATRIX_GRP0DST0SRC2CTRL0 = 62
WAVV_PFXMATRIX_GRP0DST0SRC2CTRL1 = 63
WAVV_PFXMATRIX_GRP0DST0SRC2CTRL2 = 64
WAVV_PFXMATRIX_GRP0DST0SRC3CTRL0 = 65
WAVV_PFXMATRIX_GRP0DST0SRC3CTRL1 = 66
WAVV_PFXMATRIX_GRP0DST0SRC3CTRL2 = 67
WAVV_PFXMATRIX_GRP0DST1SRC0CTRL0 = 68
WAVV_PFXMATRIX_GRP0DST1SRC0CTRL1 = 69
WAVV_PFXMATRIX_GRP0DST1SRC0CTRL2 = 70
WAVV_PFXMATRIX_GRP0DST1SRC1CTRL0 = 71
WAVV_PFXMATRIX_GRP0DST1SRC1CTRL1 = 72
WAVV_PFXMATRIX_GRP0DST1SRC1CTRL2 = 73
WAVV_PFXMATRIX_GRP0DST1SRC2CTRL0 = 74
WAVV_PFXMATRIX_GRP0DST1SRC2CTRL1 = 75
WAVV_PFXMATRIX_GRP0DST1SRC2CTRL2 = 76
WAVV_PFXMATRIX_GRP0DST1SRC3CTRL0 = 77
WAVV_PFXMATRIX_GRP0DST1SRC3CTRL1 = 78
WAVV_PFXMATRIX_GRP0DST1SRC3CTRL2 = 79
WAVV_PFXMATRIX_GRP0DST2SRC0CTRL0 = 80
WAVV_PFXMATRIX_GRP0DST2SRC0CTRL1 = 81
WAVV_PFXMATRIX_GRP0DST2SRC0CTRL2 = 82
WAVV_PFXMATRIX_GRP0DST2SRC1CTRL0 = 83
WAVV_PFXMATRIX_GRP0DST2SRC1CTRL1 = 84
WAVV_PFXMATRIX_GRP0DST2SRC1CTRL2 = 85
WAVV_PFXMATRIX_GRP0DST2SRC2CTRL0 = 86
WAVV_PFXMATRIX_GRP0DST2SRC2CTRL1 = 87
WAVV_PFXMATRIX_GRP0DST2SRC2CTRL2 = 88
WAVV_PFXMATRIX_GRP0DST2SRC3CTRL0 = 89
WAVV_PFXMATRIX_GRP0DST2SRC3CTRL1 = 90
WAVV_PFXMATRIX_GRP0DST2SRC3CTRL2 = 91
WAVV_PFXMATRIX_GRP0DST3SRC0CTRL0 = 92
WAVV_PFXMATRIX_GRP0DST3SRC0CTRL1 = 93
WAVV_PFXMATRIX_GRP0DST3SRC0CTRL2 = 94
WAVV_PFXMATRIX_GRP0DST3SRC1CTRL0 = 95
WAVV_PFXMATRIX_GRP0DST3SRC1CTRL1 = 96
WAVV_PFXMATRIX_GRP0DST3SRC1CTRL2 = 97
WAVV_PFXMATRIX_GRP0DST3SRC2CTRL0 = 98
WAVV_PFXMATRIX_GRP0DST3SRC2CTRL1 = 99
WAVV_PFXMATRIX_GRP0DST3SRC2CTRL2 = 100
WAVV_PFXMATRIX_GRP0DST3SRC3CTRL0 = 101
WAVV_PFXMATRIX_GRP0DST3SRC3CTRL1 = 102
WAVV_PFXMATRIX_GRP0DST3SRC3CTRL2 = 103
#End PolyFX Mod Matrix
WAYV_ADSR1_CHECKBOX = 105
WAYV_ADSR2_CHECKBOX = 106
WAYV_LFO_AMP = 107
WAYV_LFO_PITCH = 108
WAYV_PITCH_ENV_AMT = 109
WAYV_OSC2_UNISON_VOICES = 110
WAYV_OSC2_UNISON_SPREAD = 111
WAYV_LFO_AMOUNT = 112
WAYV_OSC3_TYPE = 113
WAYV_OSC3_PITCH = 114
WAYV_OSC3_TUNE = 115
WAYV_OSC3_VOLUME = 116
WAYV_OSC3_UNISON_VOICES = 117
WAYV_OSC3_UNISON_SPREAD = 118
WAYV_OSC1_FM1 = 119
WAYV_OSC1_FM2 = 120
WAYV_OSC1_FM3 = 121
WAYV_OSC2_FM1 = 122
WAYV_OSC2_FM2 = 123
WAYV_OSC2_FM3 = 124
WAYV_OSC3_FM1 = 125
WAYV_OSC3_FM2 = 126
WAYV_OSC3_FM3 = 127
WAYV_ATTACK3 = 128
WAYV_DECAY3 = 129
WAYV_SUSTAIN3 = 130
WAYV_RELEASE3 = 131
WAYV_ADSR3_CHECKBOX = 132

WAVV_PFXMATRIX_GRP0DST0SRC4CTRL0 = 133
WAVV_PFXMATRIX_GRP0DST0SRC4CTRL1 = 134
WAVV_PFXMATRIX_GRP0DST0SRC4CTRL2 = 135
WAVV_PFXMATRIX_GRP0DST1SRC4CTRL0 = 136
WAVV_PFXMATRIX_GRP0DST1SRC4CTRL1 = 137
WAVV_PFXMATRIX_GRP0DST1SRC4CTRL2 = 138
WAVV_PFXMATRIX_GRP0DST2SRC4CTRL0 = 139
WAVV_PFXMATRIX_GRP0DST2SRC4CTRL1 = 140
WAVV_PFXMATRIX_GRP0DST2SRC4CTRL2 = 141
WAVV_PFXMATRIX_GRP0DST3SRC4CTRL0 = 142
WAVV_PFXMATRIX_GRP0DST3SRC4CTRL1 = 143
WAVV_PFXMATRIX_GRP0DST3SRC4CTRL2 = 144

WAVV_PFXMATRIX_GRP0DST0SRC5CTRL0 = 145
WAVV_PFXMATRIX_GRP0DST0SRC5CTRL1 = 146
WAVV_PFXMATRIX_GRP0DST0SRC5CTRL2 = 147
WAVV_PFXMATRIX_GRP0DST1SRC5CTRL0 = 148
WAVV_PFXMATRIX_GRP0DST1SRC5CTRL1 = 149
WAVV_PFXMATRIX_GRP0DST1SRC5CTRL2 = 150
WAVV_PFXMATRIX_GRP0DST2SRC5CTRL0 = 151
WAVV_PFXMATRIX_GRP0DST2SRC5CTRL1 = 152
WAVV_PFXMATRIX_GRP0DST2SRC5CTRL2 = 153
WAVV_PFXMATRIX_GRP0DST3SRC5CTRL0 = 154
WAVV_PFXMATRIX_GRP0DST3SRC5CTRL1 = 155
WAVV_PFXMATRIX_GRP0DST3SRC5CTRL2 = 156
WAYV_PERC_ENV_TIME1 = 157
WAYV_PERC_ENV_PITCH1 = 158
WAYV_PERC_ENV_TIME2 = 159
WAYV_PERC_ENV_PITCH2 = 160
WAYV_PERC_ENV_ON = 161
WAYV_RAMP_CURVE = 162
WAYV_MONO_MODE = 163

WAYV_OSC4_TYPE = 164
WAYV_OSC4_PITCH = 165
WAYV_OSC4_TUNE = 166
WAYV_OSC4_VOLUME = 167
WAYV_OSC4_UNISON_VOICES = 168
WAYV_OSC4_UNISON_SPREAD = 169
WAYV_OSC1_FM4 = 170
WAYV_OSC2_FM4 = 171
WAYV_OSC3_FM4 = 172
WAYV_OSC4_FM1 = 173
WAYV_OSC4_FM2 = 174
WAYV_OSC4_FM3 = 175
WAYV_OSC4_FM4 = 176
WAYV_ATTACK4 = 177
WAYV_DECAY4 =  178
WAYV_SUSTAIN4 = 179
WAYV_RELEASE4 = 180
WAYV_ADSR4_CHECKBOX = 181

WAYV_FM_MACRO1 = 182
WAYV_FM_MACRO1_OSC1_FM1 = 183
WAYV_FM_MACRO1_OSC1_FM2 = 184
WAYV_FM_MACRO1_OSC1_FM3 = 185
WAYV_FM_MACRO1_OSC1_FM4 = 186
WAYV_FM_MACRO1_OSC2_FM1 = 187
WAYV_FM_MACRO1_OSC2_FM2 = 188
WAYV_FM_MACRO1_OSC2_FM3 = 189
WAYV_FM_MACRO1_OSC2_FM4 = 190
WAYV_FM_MACRO1_OSC3_FM1 = 191
WAYV_FM_MACRO1_OSC3_FM2 = 192
WAYV_FM_MACRO1_OSC3_FM3 = 193
WAYV_FM_MACRO1_OSC3_FM4 = 194
WAYV_FM_MACRO1_OSC4_FM1 = 195
WAYV_FM_MACRO1_OSC4_FM2 = 196
WAYV_FM_MACRO1_OSC4_FM3 = 197
WAYV_FM_MACRO1_OSC4_FM4 = 198

WAYV_FM_MACRO2 = 199
WAYV_FM_MACRO2_OSC1_FM1 = 200
WAYV_FM_MACRO2_OSC1_FM2 = 201
WAYV_FM_MACRO2_OSC1_FM3 = 202
WAYV_FM_MACRO2_OSC1_FM4 = 203
WAYV_FM_MACRO2_OSC2_FM1 = 204
WAYV_FM_MACRO2_OSC2_FM2 = 205
WAYV_FM_MACRO2_OSC2_FM3 = 206
WAYV_FM_MACRO2_OSC2_FM4 = 207
WAYV_FM_MACRO2_OSC3_FM1 = 208
WAYV_FM_MACRO2_OSC3_FM2 = 209
WAYV_FM_MACRO2_OSC3_FM3 = 210
WAYV_FM_MACRO2_OSC3_FM4 = 211
WAYV_FM_MACRO2_OSC4_FM1 = 212
WAYV_FM_MACRO2_OSC4_FM2 = 213
WAYV_FM_MACRO2_OSC4_FM3 = 214
WAYV_FM_MACRO2_OSC4_FM4 = 215

WAYV_LFO_PHASE = 216

WAYV_FM_MACRO1_OSC1_VOL = 217
WAYV_FM_MACRO1_OSC2_VOL = 218
WAYV_FM_MACRO1_OSC3_VOL = 219
WAYV_FM_MACRO1_OSC4_VOL = 220

WAYV_FM_MACRO2_OSC1_VOL = 221
WAYV_FM_MACRO2_OSC2_VOL = 222
WAYV_FM_MACRO2_OSC3_VOL = 223
WAYV_FM_MACRO2_OSC4_VOL = 224
WAYV_LFO_PITCH_FINE = 225
WAYV_ADSR_PREFX = 226

WAYV_ADSR1_DELAY = 227
WAYV_ADSR2_DELAY = 228
WAYV_ADSR3_DELAY = 229
WAYV_ADSR4_DELAY = 230

WAYV_ADSR1_HOLD = 231
WAYV_ADSR2_HOLD = 232
WAYV_ADSR3_HOLD = 233
WAYV_ADSR4_HOLD = 234

WAYV_PFX_ADSR_DELAY = 235
WAYV_PFX_ADSR_F_DELAY = 236
WAYV_PFX_ADSR_HOLD = 237
WAYV_PFX_ADSR_F_HOLD = 238
WAYV_HOLD_MAIN  = 239

WAYV_DELAY_NOISE = 240
WAYV_ATTACK_NOISE = 241
WAYV_HOLD_NOISE = 242
WAYV_DECAY_NOISE = 243
WAYV_SUSTAIN_NOISE = 244
WAYV_RELEASE_NOISE = 245
WAYV_ADSR_NOISE_ON = 246

WAYV_DELAY_LFO = 247
WAYV_ATTACK_LFO = 248
WAYV_HOLD_LFO = 249
WAYV_DECAY_LFO = 250
WAYV_SUSTAIN_LFO = 251
WAYV_RELEASE_LFO = 252
WAYV_ADSR_LFO_ON = 253


WAYV_OSC5_TYPE = 254
WAYV_OSC5_PITCH = 255
WAYV_OSC5_TUNE = 256
WAYV_OSC5_VOLUME = 257
WAYV_OSC5_UNISON_VOICES = 258
WAYV_OSC5_UNISON_SPREAD = 259
WAYV_OSC1_FM5 = 260
WAYV_OSC2_FM5 = 261
WAYV_OSC3_FM5 = 262
WAYV_OSC4_FM5 = 263
WAYV_OSC5_FM5 = 264
WAYV_OSC6_FM5 = 265
WAYV_ADSR5_DELAY = 266
WAYV_ATTACK5 = 267
WAYV_ADSR5_HOLD = 268
WAYV_DECAY5 = 269
WAYV_SUSTAIN5 = 270
WAYV_RELEASE5 = 271
WAYV_ADSR5_CHECKBOX = 272

WAYV_OSC6_TYPE = 273
WAYV_OSC6_PITCH = 274
WAYV_OSC6_TUNE = 275
WAYV_OSC6_VOLUME = 276
WAYV_OSC6_UNISON_VOICES = 277
WAYV_OSC6_UNISON_SPREAD = 278
WAYV_OSC1_FM6 = 279
WAYV_OSC2_FM6 = 280
WAYV_OSC3_FM6 = 281
WAYV_OSC4_FM6 = 282
WAYV_OSC5_FM6 = 283
WAYV_OSC6_FM6 = 284
WAYV_ADSR6_DELAY = 285
WAYV_ATTACK6 = 286
WAYV_ADSR6_HOLD = 287
WAYV_DECAY6 = 288
WAYV_SUSTAIN6 = 289
WAYV_RELEASE6 = 290
WAYV_ADSR6_CHECKBOX = 291


WAYV_FM_MACRO1_OSC1_FM5 = 292
WAYV_FM_MACRO1_OSC2_FM5 = 293
WAYV_FM_MACRO1_OSC3_FM5 = 294
WAYV_FM_MACRO1_OSC4_FM5 = 295
WAYV_FM_MACRO1_OSC5_FM5 = 296
WAYV_FM_MACRO1_OSC6_FM5 = 297

WAYV_FM_MACRO1_OSC1_FM6 = 298
WAYV_FM_MACRO1_OSC2_FM6 = 299
WAYV_FM_MACRO1_OSC3_FM6 = 300
WAYV_FM_MACRO1_OSC4_FM6 = 301
WAYV_FM_MACRO1_OSC5_FM6 = 302
WAYV_FM_MACRO1_OSC6_FM6 = 303

WAYV_FM_MACRO1_OSC5_FM1 = 304
WAYV_FM_MACRO1_OSC5_FM2 = 305
WAYV_FM_MACRO1_OSC5_FM3 = 306
WAYV_FM_MACRO1_OSC5_FM4 = 307

WAYV_FM_MACRO1_OSC6_FM1 = 308
WAYV_FM_MACRO1_OSC6_FM2 = 309
WAYV_FM_MACRO1_OSC6_FM3 = 310
WAYV_FM_MACRO1_OSC6_FM4 = 311

WAYV_FM_MACRO1_OSC5_VOL = 312
WAYV_FM_MACRO1_OSC6_VOL = 313

WAYV_FM_MACRO2_OSC1_FM5 = 314
WAYV_FM_MACRO2_OSC2_FM5 = 315
WAYV_FM_MACRO2_OSC3_FM5 = 316
WAYV_FM_MACRO2_OSC4_FM5 = 317
WAYV_FM_MACRO2_OSC5_FM5 = 318
WAYV_FM_MACRO2_OSC6_FM5 = 319

WAYV_FM_MACRO2_OSC1_FM6 = 320
WAYV_FM_MACRO2_OSC2_FM6 = 321
WAYV_FM_MACRO2_OSC3_FM6 = 322
WAYV_FM_MACRO2_OSC4_FM6 = 323
WAYV_FM_MACRO2_OSC5_FM6 = 324
WAYV_FM_MACRO2_OSC6_FM6 = 325

WAYV_FM_MACRO2_OSC5_FM1 = 326
WAYV_FM_MACRO2_OSC5_FM2 = 327
WAYV_FM_MACRO2_OSC5_FM3 = 328
WAYV_FM_MACRO2_OSC5_FM4 = 329

WAYV_FM_MACRO2_OSC6_FM1 = 330
WAYV_FM_MACRO2_OSC6_FM2 = 331
WAYV_FM_MACRO2_OSC6_FM3 = 332
WAYV_FM_MACRO2_OSC6_FM4 = 333

WAYV_FM_MACRO2_OSC5_VOL = 334
WAYV_FM_MACRO2_OSC6_VOL = 335

WAYV_OSC5_FM1 = 336
WAYV_OSC5_FM2 = 337
WAYV_OSC5_FM3 = 338
WAYV_OSC5_FM4 = 339

WAYV_OSC6_FM1 = 340
WAYV_OSC6_FM2 = 341
WAYV_OSC6_FM3 = 342
WAYV_OSC6_FM4 = 343
WAYV_NOISE_PREFX = 344

WAVV_PFXMATRIX_GRP0DST0SRC6CTRL0 = 345
WAVV_PFXMATRIX_GRP0DST0SRC6CTRL1 = 346
WAVV_PFXMATRIX_GRP0DST0SRC6CTRL2 = 347
WAVV_PFXMATRIX_GRP0DST1SRC6CTRL0 = 348
WAVV_PFXMATRIX_GRP0DST1SRC6CTRL1 = 349
WAVV_PFXMATRIX_GRP0DST1SRC6CTRL2 = 350
WAVV_PFXMATRIX_GRP0DST2SRC6CTRL0 = 351
WAVV_PFXMATRIX_GRP0DST2SRC6CTRL1 = 352
WAVV_PFXMATRIX_GRP0DST2SRC6CTRL2 = 353
WAVV_PFXMATRIX_GRP0DST3SRC6CTRL0 = 354
WAVV_PFXMATRIX_GRP0DST3SRC6CTRL1 = 355
WAVV_PFXMATRIX_GRP0DST3SRC6CTRL2 = 356

WAVV_PFXMATRIX_GRP0DST0SRC7CTRL0 = 357
WAVV_PFXMATRIX_GRP0DST0SRC7CTRL1 = 358
WAVV_PFXMATRIX_GRP0DST0SRC7CTRL2 = 359
WAVV_PFXMATRIX_GRP0DST1SRC7CTRL0 = 360
WAVV_PFXMATRIX_GRP0DST1SRC7CTRL1 = 361
WAVV_PFXMATRIX_GRP0DST1SRC7CTRL2 = 362
WAVV_PFXMATRIX_GRP0DST2SRC7CTRL0 = 363
WAVV_PFXMATRIX_GRP0DST2SRC7CTRL1 = 364
WAVV_PFXMATRIX_GRP0DST2SRC7CTRL2 = 365
WAVV_PFXMATRIX_GRP0DST3SRC7CTRL0 = 366
WAVV_PFXMATRIX_GRP0DST3SRC7CTRL1 = 367
WAVV_PFXMATRIX_GRP0DST3SRC7CTRL2 = 368

WAYV_MIN_NOTE = 369
WAYV_MAX_NOTE = 370
WAYV_MASTER_PITCH = 371

WAYV_ADSR_LIN_MAIN = 372


WAYV_PORT_MAP = {
    "Master Attack": WAYV_ATTACK_MAIN,
    "Master Hold": WAYV_HOLD_MAIN,
    "Master Decay": WAYV_DECAY_MAIN,
    "Master Sustain": WAYV_SUSTAIN_MAIN,
    "Master Release": WAYV_RELEASE_MAIN,
    "Noise Amp": WAYV_OSC1_TYPE,
    "Master Glide": 18,
    "Osc1 Attack": WAYV_ATTACK1,
    "Osc1 Decay": WAYV_DECAY1,
    "Osc1 Sustain": WAYV_SUSTAIN1,
    "Osc1 Release": WAYV_RELEASE1,
    "Osc2 Attack": WAYV_ATTACK2,
    "Osc2 Decay": WAYV_DECAY2,
    "Osc2 Sustain": WAYV_SUSTAIN2,
    "Osc2 Release": WAYV_RELEASE2,
    "PFX ADSR1 Attack": 28,
    "PFX ADSR1 Decay": 29,
    "PFX ADSR1 Sustain": "30",
    "PFX ADSR1 Release": "31",
    "PFX ADSR2 Attack": "32",
    "PFX ADSR2 Decay": "33",
    "PFX ADSR2 Sustain": "34",
    "PFX ADSR2 Release": "35",
    "Pitch Env Time": "37",
    "LFO Freq": "38",
    "FX0 Knob0": "40",
    "FX0 Knob1": "41",
    "FX0 Knob2": "42",
    "FX1 Knob0": "44",
    "FX1 Knob1": "45",
    "FX1 Knob2": "46",
    "FX2 Knob0": "48",
    "FX2 Knob1": "49",
    "FX2 Knob2": "50",
    "FX3 Knob0": "52",
    "FX3 Knob1": "53",
    "FX3 Knob2": "54",
    "LFO Amp": "107",
    "LFO Pitch": "108",
    "LFO Pitch Fine": WAYV_LFO_PITCH_FINE,
    "Pitch Env Amt": "109",
    "LFO Amount": "112",
    "Osc1 FM1": WAYV_OSC1_FM1,
    "Osc1 FM2": WAYV_OSC1_FM2,
    "Osc1 FM3": WAYV_OSC1_FM3,
    "Osc1 FM4": WAYV_OSC1_FM4,
    "Osc1 FM5": WAYV_OSC1_FM5,
    "Osc1 FM6": WAYV_OSC1_FM6,
    "Osc2 FM1": WAYV_OSC2_FM1,
    "Osc2 FM2": WAYV_OSC2_FM2,
    "Osc2 FM3": WAYV_OSC2_FM3,
    "Osc2 FM4": WAYV_OSC2_FM4,
    "Osc2 FM5": WAYV_OSC2_FM5,
    "Osc2 FM6": WAYV_OSC2_FM6,
    "Osc3 FM1": WAYV_OSC3_FM1,
    "Osc3 FM2": WAYV_OSC3_FM2,
    "Osc3 FM3": WAYV_OSC3_FM3,
    "Osc3 FM4": WAYV_OSC3_FM4,
    "Osc3 FM5": WAYV_OSC3_FM5,
    "Osc3 FM6": WAYV_OSC3_FM6,
    "Osc4 FM1": WAYV_OSC4_FM1,
    "Osc4 FM2": WAYV_OSC4_FM2,
    "Osc4 FM3": WAYV_OSC4_FM3,
    "Osc4 FM4": WAYV_OSC4_FM4,
    "Osc4 FM5": WAYV_OSC4_FM5,
    "Osc4 FM6": WAYV_OSC4_FM6,
    "Osc5 FM1": WAYV_OSC5_FM1,
    "Osc5 FM2": WAYV_OSC5_FM2,
    "Osc5 FM3": WAYV_OSC5_FM3,
    "Osc5 FM4": WAYV_OSC5_FM4,
    "Osc5 FM5": WAYV_OSC5_FM5,
    "Osc5 FM6": WAYV_OSC5_FM6,
    "Osc6 FM1": WAYV_OSC6_FM1,
    "Osc6 FM2": WAYV_OSC6_FM2,
    "Osc6 FM3": WAYV_OSC6_FM3,
    "Osc6 FM4": WAYV_OSC6_FM4,
    "Osc6 FM5": WAYV_OSC6_FM5,
    "Osc6 FM6": WAYV_OSC6_FM6,
    "Osc3 Attack": WAYV_ATTACK3,
    "Osc3 Decay": WAYV_DECAY3,
    "Osc3 Sustain": WAYV_SUSTAIN3,
    "Osc3 Release": WAYV_RELEASE3,
    "FM Macro 1": WAYV_FM_MACRO1,
    "FM Macro 2": WAYV_FM_MACRO2,
    "Osc4 Attack": WAYV_ATTACK4,
    "Osc4 Decay": WAYV_DECAY4,
    "Osc4 Sustain": WAYV_SUSTAIN4,
    "Osc4 Release": WAYV_RELEASE4,
    "Osc5 Attack": WAYV_ATTACK5,
    "Osc5 Decay": WAYV_DECAY5,
    "Osc5 Sustain": WAYV_SUSTAIN5,
    "Osc5 Release": WAYV_RELEASE5,
    "Osc6 Attack": WAYV_ATTACK6,
    "Osc6 Decay": WAYV_DECAY6,
    "Osc6 Sustain": WAYV_SUSTAIN6,
    "Osc6 Release": WAYV_RELEASE6,
    "Osc1 Delay": WAYV_ADSR1_DELAY,
    "Osc2 Delay": WAYV_ADSR2_DELAY,
    "Osc3 Delay": WAYV_ADSR3_DELAY,
    "Osc4 Delay": WAYV_ADSR4_DELAY,
    "Osc5 Delay": WAYV_ADSR5_DELAY,
    "Osc6 Delay": WAYV_ADSR6_DELAY,
    "Osc1 Hold": WAYV_ADSR1_HOLD,
    "Osc2 Hold": WAYV_ADSR2_HOLD,
    "Osc3 Hold": WAYV_ADSR3_HOLD,
    "Osc4 Hold": WAYV_ADSR4_HOLD,
    "Osc5 Hold": WAYV_ADSR5_HOLD,
    "Osc6 Hold": WAYV_ADSR6_HOLD,
}


class wayv_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, *args, **kwargs):
        pydaw_abstract_plugin_ui.__init__(self, *args, **kwargs)
        self._plugin_name = "WAYV"
        self.is_instrument = True

        f_osc_types = [_("Off"),
            #Saw-like waves
            _("Plain Saw"), _("SuperbSaw"), _("Viral Saw"), _("Soft Saw"),
            _("Mid Saw"), _("Lush Saw"),
            #Square-like waves
            _("Evil Square"), _("Punchy Square"), _("Soft Square"),
            #Glitchy and distorted waves
            _("Pink Glitch"), _("White Glitch"), _("Acid"), _("Screetch"),
            #Sine and triangle-like waves
            _("Thick Bass"), _("Rattler"), _("Deep Saw"), _("Sine"),
            #The custom additive oscillator tab
            _("(Additive 1)"), _("(Additive 2)"), _("(Additive 3)")
        ]

        self.fm_knobs = []
        self.fm_origin = None
        self.fm_macro_spinboxes = [[] for x in range(2)]

        f_lfo_types = [_("Off"), _("Sine"), _("Triangle")]
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.osc_tab = QWidget()
        self.osc_tab_vlayout = QVBoxLayout(self.osc_tab)
        self.osc_scrollarea = QScrollArea()
        self.osc_scrollarea.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.osc_scrollarea.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)
        self.tab_widget.addTab(self.osc_tab, _("Oscillators"))
        self.fm_tab = QWidget()
        self.tab_widget.addTab(self.fm_tab, _("FM"))
        self.modulation_tab = QWidget()
        self.tab_widget.addTab(self.modulation_tab, _("Modulation"))
        self.poly_fx_tab = QWidget()
        self.tab_widget.addTab(self.poly_fx_tab, _("PolyFX"))
        self.osc_tab_widget = QWidget()
        self.osc_tab_widget.setObjectName("plugin_ui")
        self.osc_scrollarea.setWidget(self.osc_tab_widget)
        self.osc_scrollarea.setWidgetResizable(True)
        self.oscillator_layout = QVBoxLayout(self.osc_tab_widget)
        self.preset_manager = pydaw_preset_manager_widget(
            self.get_plugin_name(), self.configure_dict,
            self.reconfigure_plugin)
        self.preset_hlayout = QHBoxLayout()
        self.preset_hlayout.addWidget(self.preset_manager.group_box)
        self.preset_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))
        self.osc_tab_vlayout.addLayout(self.preset_hlayout)
        self.osc_tab_vlayout.addWidget(self.osc_scrollarea)

        self.hlayout0 = QHBoxLayout()
        self.oscillator_layout.addLayout(self.hlayout0)
        self.hlayout0.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))
        f_knob_size = 39

        for f_i in range(1, 7):
            f_hlayout1 = QHBoxLayout()
            self.oscillator_layout.addLayout(f_hlayout1)
            f_osc1 = pydaw_osc_widget(
                f_knob_size,
                getattr(sys.modules[__name__], "WAYV_OSC{}_PITCH".format(f_i)),
                getattr(sys.modules[__name__], "WAYV_OSC{}_TUNE".format(f_i)),
                getattr(sys.modules[__name__],
                        "WAYV_OSC{}_VOLUME".format(f_i)),
                getattr(sys.modules[__name__], "WAYV_OSC{}_TYPE".format(f_i)),
                f_osc_types,
                self.plugin_rel_callback, self.plugin_val_callback,
                _("Oscillator {}".format(f_i)),
                self.port_dict, self.preset_manager,
                1 if f_i == 1 else 0)
            f_osc1.osc_type_combobox.control.setMaxVisibleItems(
                len(f_osc_types))
            f_osc1.pitch_knob.control.setRange(-72, 72)
            f_osc1_uni_voices = pydaw_knob_control(
                f_knob_size, _("Unison"),
                getattr(
                    sys.modules[__name__],
                    "WAYV_OSC{}_UNISON_VOICES".format(f_i)),
                self.plugin_rel_callback, self.plugin_val_callback,
                1, 7, 1, KC_INTEGER, self.port_dict, self.preset_manager)
            f_osc1_uni_voices.add_to_grid_layout(f_osc1.grid_layout, 4)
            f_osc1_uni_spread = pydaw_knob_control(
                f_knob_size, _("Spread"), getattr(sys.modules[__name__],
                "WAYV_OSC{}_UNISON_SPREAD".format(f_i)),
                self.plugin_rel_callback, self.plugin_val_callback,
                0, 100, 50, KC_DECIMAL, self.port_dict, self.preset_manager)
            f_osc1_uni_spread.add_to_grid_layout(f_osc1.grid_layout, 5)

            f_hlayout1.addWidget(f_osc1.group_box)

            f_adsr_amp1 = pydaw_adsr_widget(
                f_knob_size, True,
                getattr(sys.modules[__name__], "WAYV_ATTACK{}".format(f_i)),
                getattr(sys.modules[__name__], "WAYV_DECAY{}".format(f_i)),
                getattr(sys.modules[__name__], "WAYV_SUSTAIN{}".format(f_i)),
                getattr(sys.modules[__name__], "WAYV_RELEASE{}".format(f_i)),
                _("DAHDSR Osc{}".format(f_i)),
                self.plugin_rel_callback,
                self.plugin_val_callback,
                self.port_dict, self.preset_manager,
                a_knob_type=KC_LOG_TIME,
                a_delay_port=
                getattr(sys.modules[__name__], "WAYV_ADSR{}_DELAY".format(f_i)),
                a_hold_port=
                getattr(sys.modules[__name__], "WAYV_ADSR{}_HOLD".format(f_i)))
            f_hlayout1.addWidget(f_adsr_amp1.groupbox)

            f_adsr_amp1_checkbox = pydaw_checkbox_control(
                _("On"), getattr(sys.modules[__name__],
                "WAYV_ADSR{}_CHECKBOX".format(f_i)),
                self.plugin_rel_callback, self.plugin_val_callback,
                self.port_dict, self.preset_manager)
            f_adsr_amp1_checkbox.add_to_grid_layout(f_adsr_amp1.layout, 15)

            f_hlayout1.addItem(
                QSpacerItem(1, 1, QSizePolicy.Expanding))


        ######################


        self.fm_vlayout = QVBoxLayout(self.fm_tab)

        # FM Matrix

        self.fm_matrix_hlayout = QHBoxLayout()
        self.fm_vlayout.addLayout(self.fm_matrix_hlayout)
        self.fm_matrix_hlayout.addWidget(QLabel("FM Matrix"))
        self.fm_matrix = QTableWidget()

        self.fm_matrix.setCornerButtonEnabled(False)
        self.fm_matrix.setRowCount(6)
        self.fm_matrix.setColumnCount(6)
        self.fm_matrix.setFixedHeight(228)
        self.fm_matrix.setFixedWidth(447)
        f_fm_src_matrix_labels = ["From Osc{}".format(x) for x in range(1, 7)]
        f_fm_dest_matrix_labels = ["To\nOsc{}".format(x) for x in range(1, 7)]
        self.fm_matrix.setHorizontalHeaderLabels(f_fm_dest_matrix_labels)
        self.fm_matrix.setVerticalHeaderLabels(f_fm_src_matrix_labels)
        self.fm_matrix.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.fm_matrix.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.fm_matrix.horizontalHeader().setSectionResizeMode(
            QHeaderView.Fixed)
        self.fm_matrix.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        self.fm_matrix_hlayout.addWidget(self.fm_matrix)

        for f_i in range(6):
            for f_i2 in range(6):
                f_port = getattr(
                    sys.modules[__name__],
                    "WAYV_OSC{}_FM{}".format(f_i2 + 1, f_i + 1))
                f_spinbox = pydaw_spinbox_control(
                    None, f_port,
                    self.plugin_rel_callback, self.plugin_val_callback,
                    0, 100, 0, KC_NONE, self.port_dict, self.preset_manager)
                self.fm_matrix.setCellWidget(f_i, f_i2, f_spinbox.control)
                self.fm_knobs.append(f_spinbox)

        self.fm_matrix.resizeColumnsToContents()

        self.fm_matrix_button = QPushButton(_("Menu"))
        self.fm_matrix_hlayout.addWidget(
            self.fm_matrix_button,
            alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.fm_matrix_menu = QMenu(self.widget)
        self.fm_matrix_button.setMenu(self.fm_matrix_menu)
        f_origin_action = self.fm_matrix_menu.addAction(_("Set Origin"))
        f_origin_action.triggered.connect(self.set_fm_origin)
        f_return_action = self.fm_matrix_menu.addAction(_("Return to Origin"))
        f_return_action.triggered.connect(self.return_to_origin)
        self.fm_matrix_menu.addSeparator()
        f_macro1_action = self.fm_matrix_menu.addAction(_("Set Macro 1 End"))
        f_macro1_action.triggered.connect(self.set_fm_macro1_end)
        f_macro2_action = self.fm_matrix_menu.addAction(_("Set Macro 2 End"))
        f_macro2_action.triggered.connect(self.set_fm_macro2_end)
        self.fm_matrix_menu.addSeparator()
        f_return_macro1_action = self.fm_matrix_menu.addAction(
            _("Return to Macro 1 End"))
        f_return_macro1_action.triggered.connect(self.return_fm_macro1_end)
        f_return_macro2_action = self.fm_matrix_menu.addAction(
            _("Return to Macro 2 End"))
        f_return_macro2_action.triggered.connect(self.return_fm_macro2_end)
        self.fm_matrix_menu.addSeparator()
        f_clear_fm_action = self.fm_matrix_menu.addAction(_("Clear All"))
        f_clear_fm_action.triggered.connect(self.clear_all)

        self.fm_matrix_hlayout.addWidget(
            QLabel(_("FM\nModulation\nMacros")))

        self.fm_macro_knobs_gridlayout = QGridLayout()
        self.fm_macro_knobs_gridlayout.addItem(
            QSpacerItem(1, 1, vPolicy=QSizePolicy.Expanding),
            10, 0)

        self.fm_matrix_hlayout.addLayout(self.fm_macro_knobs_gridlayout)

        self.fm_matrix_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))

        self.fm_macro_knobs = []
        self.osc_amp_mod_matrix_spinboxes = [[] for x in range(2)]

        self.fm_macro_labels_hlayout = QHBoxLayout()
        self.fm_vlayout.addLayout(self.fm_macro_labels_hlayout)
        self.fm_macro_matrix_hlayout = QHBoxLayout()
        self.fm_vlayout.addLayout(self.fm_macro_matrix_hlayout)

        for f_i in range(2):
            f_port = getattr(
                sys.modules[__name__], "WAYV_FM_MACRO{}".format(f_i + 1))
            f_macro = pydaw_knob_control(
                f_knob_size, _("Macro{}".format(f_i + 1)), f_port,
                self.plugin_rel_callback, self.plugin_val_callback,
                0, 100, 0, KC_DECIMAL, self.port_dict, self.preset_manager)
            f_macro.add_to_grid_layout(self.fm_macro_knobs_gridlayout, f_i)
            self.fm_macro_knobs.append(f_macro)

            f_fm_macro_matrix = QTableWidget()
            self.fm_macro_labels_hlayout.addWidget(
                QLabel("Macro {}".format(f_i + 1),
                f_fm_macro_matrix), -1)

            f_fm_macro_matrix.setCornerButtonEnabled(False)
            f_fm_macro_matrix.setRowCount(7)
            f_fm_macro_matrix.setColumnCount(6)
            f_fm_macro_matrix.setFixedHeight(264)
            f_fm_macro_matrix.setFixedWidth(487)
            f_fm_src_matrix_labels = ["From Osc{}".format(x)
                for x in range(1, 7)] + ["Vol"]
            f_fm_dest_matrix_labels = ["To\nOsc{}".format(x)
                for x in range(1, 7)]
            f_fm_macro_matrix.setHorizontalHeaderLabels(
                f_fm_dest_matrix_labels)
            f_fm_macro_matrix.setVerticalHeaderLabels(f_fm_src_matrix_labels)
            f_fm_macro_matrix.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff)
            f_fm_macro_matrix.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff)
            f_fm_macro_matrix.horizontalHeader().setSectionResizeMode(
                QHeaderView.Fixed)
            f_fm_macro_matrix.verticalHeader().setSectionResizeMode(
                QHeaderView.Fixed)

            self.fm_macro_matrix_hlayout.addWidget(f_fm_macro_matrix)

            for f_i2 in range(6):
                for f_i3 in range(6):
                    f_port = getattr(
                        sys.modules[__name__],
                        "WAYV_FM_MACRO{}_OSC{}_FM{}".format(
                            f_i + 1, f_i3 + 1, f_i2 + 1))
                    f_spinbox = pydaw_spinbox_control(
                        None, f_port,
                        self.plugin_rel_callback, self.plugin_val_callback,
                        -100, 100, 0, KC_NONE, self.port_dict,
                        self.preset_manager)
                    f_fm_macro_matrix.setCellWidget(
                        f_i2, f_i3, f_spinbox.control)
                    self.fm_macro_spinboxes[f_i].append(f_spinbox)

                f_port = getattr(
                    sys.modules[__name__], "WAYV_FM_MACRO{}_OSC{}_VOL".format(
                    f_i + 1, f_i2 + 1))
                f_spinbox = pydaw_spinbox_control(
                    None, f_port,
                    self.plugin_rel_callback, self.plugin_val_callback,
                    -100, 100, 0, KC_NONE, self.port_dict, self.preset_manager)
                f_fm_macro_matrix.setCellWidget(6, f_i2, f_spinbox.control)
                self.osc_amp_mod_matrix_spinboxes[f_i].append(f_spinbox)
                f_fm_macro_matrix.resizeColumnsToContents()
        self.fm_macro_matrix_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))
        self.fm_vlayout.addItem(
            QSpacerItem(1, 1, vPolicy=QSizePolicy.Expanding))

        ############################

        self.modulation_vlayout = QVBoxLayout(self.modulation_tab)

        self.hlayout_master = QHBoxLayout()
        self.modulation_vlayout.addLayout(self.hlayout_master)
        self.master = pydaw_master_widget(
            f_knob_size, self.plugin_rel_callback,
            self.plugin_val_callback, WAYV_MASTER_VOLUME,
            WAYV_MASTER_GLIDE, WAYV_MASTER_PITCHBEND_AMT,
            self.port_dict, a_preset_mgr=self.preset_manager,
            a_poly_port=WAYV_MONO_MODE,
            a_min_note_port=WAYV_MIN_NOTE, a_max_note_port=WAYV_MAX_NOTE,
            a_pitch_port=WAYV_MASTER_PITCH)

        self.hlayout_master.addWidget(self.master.group_box)

        self.adsr_amp_main = pydaw_adsr_widget(
            f_knob_size, True, WAYV_ATTACK_MAIN,
            WAYV_DECAY_MAIN, WAYV_SUSTAIN_MAIN,
            WAYV_RELEASE_MAIN, _("AHDSR Master"),
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager,
            a_prefx_port=WAYV_ADSR_PREFX,
            a_knob_type=KC_LOG_TIME, a_hold_port=WAYV_HOLD_MAIN,
            a_lin_port=WAYV_ADSR_LIN_MAIN)
        self.hlayout_master.addWidget(self.adsr_amp_main.groupbox)

        self.perc_env = pydaw_perc_env_widget(
            f_knob_size, self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, WAYV_PERC_ENV_TIME1,
            WAYV_PERC_ENV_PITCH1, WAYV_PERC_ENV_TIME2,
            WAYV_PERC_ENV_PITCH2, WAYV_PERC_ENV_ON,
            a_preset_mgr=self.preset_manager)

        self.hlayout_master2 = QHBoxLayout()
        self.modulation_vlayout.addLayout(self.hlayout_master2)
        self.hlayout_master2.addWidget(self.perc_env.groupbox)

        self.adsr_noise = pydaw_adsr_widget(
            f_knob_size, True, WAYV_ATTACK_NOISE,
            WAYV_DECAY_NOISE, WAYV_SUSTAIN_NOISE,
            WAYV_RELEASE_NOISE, _("DAHDSR Noise"),
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager,
            a_knob_type=KC_LOG_TIME, a_hold_port=WAYV_HOLD_NOISE,
            a_delay_port=WAYV_DELAY_NOISE)
        self.hlayout_master2.addWidget(self.adsr_noise.groupbox)
        self.adsr_noise_on = pydaw_checkbox_control(
            "On", WAYV_ADSR_NOISE_ON,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager)
        self.adsr_noise_on.add_to_grid_layout(self.adsr_noise.layout, 21)

        self.groupbox_noise = QGroupBox(_("Noise"))
        self.groupbox_noise.setObjectName("plugin_groupbox")
        self.groupbox_noise_layout = QGridLayout(self.groupbox_noise)
        self.hlayout_master2.addWidget(self.groupbox_noise)
        self.noise_amp = pydaw_knob_control(
            f_knob_size, _("Vol"), WAYV_NOISE_AMP,
            self.plugin_rel_callback, self.plugin_val_callback,
            -60, 0, -30, KC_INTEGER, self.port_dict, self.preset_manager)
        self.noise_amp.add_to_grid_layout(self.groupbox_noise_layout, 0)

        self.noise_type = pydaw_combobox_control(
            87, _("Type"), WAYV_NOISE_TYPE,
            self.plugin_rel_callback, self.plugin_val_callback,
            [_("Off"), _("White"), _("Pink")], self.port_dict,
             a_preset_mgr=self.preset_manager)
        self.noise_type.control.setMaximumWidth(87)
        self.noise_type.add_to_grid_layout(self.groupbox_noise_layout, 1)

        self.noise_prefx = pydaw_checkbox_control(
            "PreFX", WAYV_NOISE_PREFX,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_preset_mgr=self.preset_manager, a_default=1)
        self.noise_prefx.add_to_grid_layout(self.groupbox_noise_layout, 6)

        self.modulation_vlayout.addItem(
            QSpacerItem(1, 1, vPolicy=QSizePolicy.Expanding))

        self.hlayout_master.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))

        self.hlayout_master2.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))

        self.modulation_vlayout.addWidget(QLabel(_("PolyFX")))

        ############################

        self.main_layout = QVBoxLayout(self.poly_fx_tab)
        self.hlayout5 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout5)
        self.hlayout6 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout6)
        #From Modulex
        self.fx0 = pydaw_modulex_single(
            _("FX0"), WAYV_FX0_KNOB0,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager, a_knob_size=f_knob_size)
        self.hlayout5.addWidget(self.fx0.group_box)
        self.fx1 = pydaw_modulex_single(
            _("FX1"), WAYV_FX1_KNOB0,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager, a_knob_size=f_knob_size)
        self.hlayout5.addWidget(self.fx1.group_box)
        self.fx2 = pydaw_modulex_single(
            _("FX2"), WAYV_FX2_KNOB0,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager, a_knob_size=f_knob_size)
        self.hlayout6.addWidget(self.fx2.group_box)
        self.fx3 = pydaw_modulex_single(
            _("FX3"), WAYV_FX3_KNOB0,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager, a_knob_size=f_knob_size)
        self.hlayout6.addWidget(self.fx3.group_box)

        self.mod_matrix = QTableWidget()
        self.mod_matrix.setCornerButtonEnabled(False)
        self.mod_matrix.setRowCount(8)
        self.mod_matrix.setColumnCount(12)
        self.mod_matrix.setFixedHeight(291)
        self.mod_matrix.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.mod_matrix.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.mod_matrix.horizontalHeader().setSectionResizeMode(
            QHeaderView.Fixed)
        self.mod_matrix.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        f_hlabels = ["FX{}\nCtrl{}".format(x, y)
            for x in range(4) for y in range(1, 4)]
        self.mod_matrix.setHorizontalHeaderLabels(f_hlabels)
        self.mod_matrix.setVerticalHeaderLabels(
            [_("DAHDSR 1"), _("DAHDSR 2"), _("Ramp Env"),
             _("LFO"), _("Pitch"), _("Velocity"),
             _("FM Macro 1"), _("FM Macro 2")])

        for f_i_dst in range(4):
            for f_i_src in range(8):
                for f_i_ctrl in range(3):
                    f_ctrl = pydaw_spinbox_control(
                        None,
                        getattr(sys.modules[__name__], "WAVV_PFXMATRIX_"
                        "GRP0DST{}SRC{}CTRL{}".format(
                        f_i_dst, f_i_src, f_i_ctrl)),
                        self.plugin_rel_callback, self.plugin_val_callback,
                        -100, 100, 0, KC_NONE, self.port_dict,
                        self.preset_manager)
                    f_x = (f_i_dst * 3) + f_i_ctrl
                    self.mod_matrix.setCellWidget(f_i_src, f_x, f_ctrl.control)

        self.main_layout.addWidget(self.mod_matrix)
        self.mod_matrix.resizeColumnsToContents()

        self.main_layout.addItem(
            QSpacerItem(1, 1, vPolicy=QSizePolicy.Expanding))

        self.hlayout7 = QHBoxLayout()
        self.modulation_vlayout.addLayout(self.hlayout7)

        self.adsr_amp = pydaw_adsr_widget(
            f_knob_size, True,
            WAYV_ATTACK_PFX1, WAYV_DECAY_PFX1,
            WAYV_SUSTAIN_PFX1, WAYV_RELEASE_PFX1,
            _("DAHDSR 1"), self.plugin_rel_callback,
            self.plugin_val_callback, self.port_dict, self.preset_manager,
            a_knob_type=KC_LOG_TIME,
            a_delay_port=WAYV_PFX_ADSR_DELAY,
            a_hold_port=WAYV_PFX_ADSR_HOLD)

        self.hlayout7.addWidget(self.adsr_amp.groupbox)

        self.adsr_filter = pydaw_adsr_widget(
            f_knob_size, False, WAYV_ATTACK_PFX2,
            WAYV_DECAY_PFX2, WAYV_SUSTAIN_PFX2,
            WAYV_RELEASE_PFX2, _("DAHDSR 2"),
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager,
            a_knob_type=KC_LOG_TIME,
            a_delay_port=WAYV_PFX_ADSR_F_DELAY,
            a_hold_port=WAYV_PFX_ADSR_F_HOLD)
        self.hlayout7.addWidget(self.adsr_filter.groupbox)

        self.pitch_env = pydaw_ramp_env_widget(
            f_knob_size,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, WAYV_RAMP_ENV_TIME,
            WAYV_PITCH_ENV_AMT, _("Ramp Env"),
            self.preset_manager, WAYV_RAMP_CURVE)
        self.pitch_env.amt_knob.name_label.setText(_("Pitch"))
        self.pitch_env.amt_knob.control.setRange(-60, 60)
        self.hlayout7.addWidget(self.pitch_env.groupbox)
        self.hlayout7.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))

        self.lfo = pydaw_lfo_widget(
            f_knob_size, self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, WAYV_LFO_FREQ,
            WAYV_LFO_TYPE, f_lfo_types,
            _("LFO"), self.preset_manager, WAYV_LFO_PHASE)

        self.lfo_hlayout = QHBoxLayout()
        self.modulation_vlayout.addLayout(self.lfo_hlayout)
        self.lfo_hlayout.addWidget(self.lfo.groupbox)

        self.lfo_amount = pydaw_knob_control(
            f_knob_size, _("Amount"), WAYV_LFO_AMOUNT,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 100, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.lfo_amount.add_to_grid_layout(self.lfo.layout, 7)

        self.lfo_amp = pydaw_knob_control(
            f_knob_size, _("Amp"), WAYV_LFO_AMP,
            self.plugin_rel_callback, self.plugin_val_callback,
            -24, 24, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.lfo_amp.add_to_grid_layout(self.lfo.layout, 8)

        self.lfo_pitch = pydaw_knob_control(
            f_knob_size, _("Pitch"), WAYV_LFO_PITCH,
            self.plugin_rel_callback, self.plugin_val_callback,
            -36, 36, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.lfo_pitch.add_to_grid_layout(self.lfo.layout, 9)

        self.lfo_pitch_fine = pydaw_knob_control(
            f_knob_size, _("Fine"), WAYV_LFO_PITCH_FINE,
            self.plugin_rel_callback, self.plugin_val_callback,
            -100, 100, 0, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.lfo_pitch_fine.add_to_grid_layout(self.lfo.layout, 10)

        self.adsr_lfo = pydaw_adsr_widget(
            f_knob_size, False, WAYV_ATTACK_LFO,
            WAYV_DECAY_LFO, WAYV_SUSTAIN_LFO,
            WAYV_RELEASE_LFO, _("DAHDSR LFO"),
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager,
            a_knob_type=KC_LOG_TIME, a_hold_port=WAYV_HOLD_LFO,
            a_delay_port=WAYV_DELAY_LFO)
        self.lfo_hlayout.addWidget(self.adsr_lfo.groupbox)
        self.adsr_lfo_on = pydaw_checkbox_control(
            "On", WAYV_ADSR_LFO_ON,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager)
        self.adsr_lfo_on.add_to_grid_layout(self.adsr_lfo.layout, 21)

        self.lfo_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))

        self.additive_osc = pydaw_custom_additive_oscillator(
            self.configure_plugin)
        self.tab_widget.addTab(self.additive_osc.widget, "Additive")

        self.open_plugin_file()
        self.set_midi_learn(WAYV_PORT_MAP)

    def open_plugin_file(self):
        pydaw_abstract_plugin_ui.open_plugin_file(self)
        self.set_fm_origin()

    def configure_plugin(self, a_key, a_message):
        self.configure_dict[a_key] = a_message
        self.configure_callback(self.plugin_uid, a_key, a_message)
        self.has_updated_controls = True

    def set_configure(self, a_key, a_message):
        self.configure_dict[a_key] = a_message
        if a_key.startswith("wayv_add_ui"):
            self.configure_dict[a_key] = a_message
            f_arr = a_message.split("|")
            self.additive_osc.set_values(int(a_key[-1]), f_arr)
        if a_key.startswith("wayv_add_phase"):
            self.configure_dict[a_key] = a_message
            f_arr = a_message.split("|")
            self.additive_osc.set_phases(int(a_key[-1]), f_arr)
        elif a_key.startswith("wayv_add_eng"):
            pass
        else:
            print("Way-V: Unknown configure message '{}'".format(a_key))

    def reconfigure_plugin(self, a_dict):
        # Clear existing sample tables
        f_ui_config_keys = ["wayv_add_ui0", "wayv_add_ui1", "wayv_add_ui2"]
        f_eng_config_keys = ["wayv_add_eng0", "wayv_add_eng1", "wayv_add_eng2"]
        f_ui_phase_keys = ["wayv_add_phase0", "wayv_add_phase1",
                           "wayv_add_phase2"]
        f_empty_ui_val = "|".join(
            [str(ADDITIVE_OSC_MIN_AMP)] * ADDITIVE_OSC_HARMONIC_COUNT)
        f_empty_eng_val = "{}|{}".format(ADDITIVE_WAVETABLE_SIZE,
            "|".join(["0.0"] * ADDITIVE_WAVETABLE_SIZE))
        for f_key in (f_ui_config_keys + f_ui_phase_keys):
            if f_key in a_dict:
                self.configure_plugin(f_key, a_dict[f_key])
                self.set_configure(f_key, a_dict[f_key])
            else:
                self.configure_plugin(f_key, f_empty_ui_val)
                self.set_configure(f_key, f_empty_ui_val)
        for f_key in f_eng_config_keys:
            if f_key in a_dict:
                self.configure_plugin(f_key, a_dict[f_key])
            else:
                self.configure_plugin(f_key, f_empty_eng_val)
        self.has_updated_controls = True

    def set_fm_origin(self):
        self.fm_origin = []
        for f_knob in self.fm_knobs:
            self.fm_origin.append(f_knob.get_value())

    def return_to_origin(self):
        for f_value, f_knob in zip(self.fm_origin, self.fm_knobs):
            f_knob.set_value(f_value, True)
        self.reset_fm_macro_knobs()

    def reset_fm_macro_knobs(self):
        for f_knob in self.fm_macro_knobs:
            f_knob.set_value(0, True)

    def set_fm_macro1_end(self):
        self.set_fm_macro_end(0)

    def set_fm_macro2_end(self):
        self.set_fm_macro_end(1)

    def set_fm_macro_end(self, a_index):
        for f_spinbox, f_knob, f_origin in zip(
        self.fm_macro_spinboxes[a_index], self.fm_knobs, self.fm_origin):
            f_value = f_knob.get_value() - f_origin
            f_value = pydaw_util.pydaw_clip_value(f_value, -100, 100)
            f_spinbox.set_value(f_value, True)

    def clear_all(self):
        for f_control in (
        self.fm_knobs + self.fm_macro_spinboxes[0] +
        self.fm_macro_spinboxes[1]):
            f_control.set_value(0, True)

    def return_fm_macro1_end(self):
        self.return_fm_macro_end(0)

    def return_fm_macro2_end(self):
        self.return_fm_macro_end(1)

    def return_fm_macro_end(self, a_index):
        for f_spinbox, f_knob, f_origin in zip(
        self.fm_macro_spinboxes[a_index], self.fm_knobs, self.fm_origin):
            f_value = f_spinbox.get_value() + f_origin
            f_value = pydaw_util.pydaw_clip_value(f_value, 0, 100)
            f_knob.set_value(f_value, True)
        self.reset_fm_macro_knobs()

