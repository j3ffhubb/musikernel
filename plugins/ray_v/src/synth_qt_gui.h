/* -*- c-basic-offset: 4 -*-  vi:set ts=8 sts=4 sw=4: */

/* synth_qt_gui.h


This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

*/

#ifndef _SYNTH_QT_GUI_H_INCLUDED_
#define _SYNTH_QT_GUI_H_INCLUDED_

#include <QFrame>
#include <QDial>
#include <QLabel>
#include <QLayout>
#include <QCheckBox>
#include <QGroupBox>
#include <QComboBox>
#include <QPushButton>
#include <QPixmap>

#include <string>
#include <stdlib.h>

#include "../../libmodsynth/widgets/presets.h"
#include "../../libmodsynth/widgets/group_box.h"
#include "../../libmodsynth/widgets/lms_combobox.h"
#include "../../libmodsynth/widgets/lms_main_layout.h"

extern "C" {
#include <lo/lo.h>
}

/*Defines ranges and other sane defaults depending on what a knob controls*/
enum e_knob_type
{
    decibels_0,
    decibels_plus_6,
    decibels_plus_12,
    decibels_plus_24,
    decibels_30_to_0,
    pitch,
    zero_to_one,
    zero_to_two,
    zero_to_four,     
    minus1_to_1,
    minus12_to_12,
    minus24_to_24,
    minus36_to_36
};

class SynthGUI : public QFrame
{
    Q_OBJECT

public:
    SynthGUI(const char * host, const char * port,
	     QByteArray controlPath, QByteArray midiPath, QByteArray programPath,
	     QByteArray exitingPath, QWidget *w = 0);
    virtual ~SynthGUI();

    bool ready() const { return m_ready; }
    void setReady(bool ready) { m_ready = ready; }

    void setHostRequestedQuit(bool r) { m_hostRequestedQuit = r; }
    
    
    void v_set_control(int, float);
    void v_control_changed(int, int, bool);
    int i_get_control(int);
    
    void v_add_knob_to_layout(QDial *, e_knob_type, int, QLabel *, QGridLayout *, QString, int, int, const char *, const char *);
    
    void v_print_port_name_to_cerr(int);
        
public slots:
    /*Event handlers for setting knob values*/
    void setAttack (float sec);
    void setDecay  (float sec);
    void setSustain(float val);
    void setRelease(float sec);
    void setTimbre (float val);
    void setRes (float val);
    void setDist (float val);
        
    void setFilterAttack (float sec);
    void setFilterDecay  (float sec);
    void setFilterSustain(float val);
    void setFilterRelease(float sec);
    
    void setNoiseAmp(float val);
    
    void setFilterEnvAmt(float val);
    void setDistWet(float val);
    void setOsc1Type(float val);
    void setOsc1Pitch(float val);
    void setOsc1Tune(float val);
    void setOsc1Volume(float val);
    void setOsc2Type(float val);
    void setOsc2Pitch(float val);
    void setOsc2Tune(float val);
    void setOsc2Volume(float val);
    void setMasterVolume(float val);
    
    void setMasterUnisonVoices(float val);
    void setMasterUnisonSpread(float val);
    void setMasterGlide(float val);
    void setMasterPitchbendAmt(float val);
    
    void setPitchEnvTime(float val);
    void setPitchEnvAmt(float val);
    
    void setProgram(float val);    
    
    void setLFOfreq(float val);
    void setLFOtype(float val);
    void setLFOamp(float val);
    void setLFOpitch(float val);
    void setLFOcutoff(float val);
    
    void aboutToQuit();
    
protected slots:
    /*Event handlers for receiving changed knob values*/
    void attackChanged (int);
    void decayChanged  (int);
    void sustainChanged(int);
    void releaseChanged(int);
    void timbreChanged (int);
    void resChanged (int);
    void distChanged (int);
        
    void filterAttackChanged (int);
    void filterDecayChanged  (int);
    void filterSustainChanged(int);
    void filterReleaseChanged(int);
    
    void noiseAmpChanged(int);

    
    void filterEnvAmtChanged(int);
    void distWetChanged(int);
    void osc1TypeChanged(int);
    void osc1PitchChanged(int);
    void osc1TuneChanged(int);
    void osc1VolumeChanged(int);
    void osc2TypeChanged(int);
    void osc2PitchChanged(int);
    void osc2TuneChanged(int);
    void osc2VolumeChanged(int);
    void masterVolumeChanged(int);
    
    void masterUnisonVoicesChanged(int);
    void masterUnisonSpreadChanged(int);
    void masterGlideChanged(int);
    void masterPitchbendAmtChanged(int);
    
    void pitchEnvTimeChanged(int);
    void pitchEnvAmtChanged(int);
    
    void programChanged(int);
    void programSaved();
    
    void LFOfreqChanged(int);
    void LFOtypeChanged(int);
    void LFOampChanged(int);
    void LFOpitchChanged(int);
    void LFOcutoffChanged(int);
    
    void test_press();
    void test_release();
    void oscRecv();
protected:
    
    LMS_main_layout * m_main_layout;
    
    LMS_group_box * m_groupbox_adsr_a;    
    LMS_knob_regular *m_attack;    
    LMS_knob_regular *m_decay;    
    LMS_knob_regular *m_sustain;
    LMS_knob_regular *m_release;
    
    LMS_group_box * m_groupbox_filter;
    LMS_knob_regular *m_timbre;        
    LMS_knob_regular *m_filter_env_amt;        
    LMS_knob_regular *m_res;
    
    LMS_group_box * m_groupbox_distortion;
    LMS_knob_regular *m_dist;
    LMS_knob_regular *m_dist_wet;
    
    LMS_group_box * m_groupbox_adsr_f;
    LMS_knob_regular *m_filter_attack;    
    LMS_knob_regular *m_filter_decay;    
    LMS_knob_regular *m_filter_sustain;    
    LMS_knob_regular *m_filter_release;
    
    LMS_group_box * m_groupbox_noise;
    LMS_knob_regular *m_noise_amp;
    
    LMS_group_box * m_groupbox_osc1;
    LMS_combobox *m_osc1_type;
    LMS_knob_regular *m_osc1_pitch;    
    LMS_knob_regular *m_osc1_tune;    
    LMS_knob_regular *m_osc1_volume;
    
    LMS_group_box * m_groupbox_osc2;
    LMS_combobox *m_osc2_type;
    LMS_knob_regular *m_osc2_pitch;    
    LMS_knob_regular *m_osc2_tune;    
    LMS_knob_regular *m_osc2_volume;
    
    LMS_group_box * m_groupbox_master;
    LMS_knob_regular *m_master_volume;    
    LMS_knob_regular *m_master_unison_voices;
    LMS_knob_regular *m_master_unison_spread;
    LMS_knob_regular *m_master_glide;
    LMS_knob_regular *m_master_pitchbend_amt;
    
    LMS_group_box * m_groupbox_pitch_env;
    LMS_knob_regular *m_pitch_env_time;
    LMS_knob_regular *m_pitch_env_amt;
    
    LMS_group_box * m_groupbox_lfo;
    LMS_knob_regular *m_lfo_freq;
    LMS_combobox *m_lfo_type;    
    LMS_knob_regular *m_lfo_amp;        
    LMS_knob_regular *m_lfo_pitch;       
    LMS_knob_regular *m_lfo_cutoff;    
    
    LMS_preset_manager * m_program;
    
    lo_address m_host;
    QByteArray m_controlPath;
    QByteArray m_midiPath;
    QByteArray m_programPath;
    QByteArray m_exitingPath;

    bool m_suppressHostUpdate;
    bool m_hostRequestedQuit;
    bool m_ready;    
};


#endif
