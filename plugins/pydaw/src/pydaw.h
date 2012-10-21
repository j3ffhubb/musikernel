/* 
 * File:   pydaw.h
 * Author: jeffh
 *
 * Types and functions specific the the IO and file system specs of PyDAW 
 */


#ifndef PYDAW_H
#define	PYDAW_H

#ifdef	__cplusplus
extern "C" {
#endif
    
#define PYDAW_CONFIGURE_KEY_SS "ss"
#define PYDAW_CONFIGURE_KEY_OS "os"
#define PYDAW_CONFIGURE_KEY_SI "si"
#define PYDAW_CONFIGURE_KEY_DI "di"
#define PYDAW_CONFIGURE_KEY_SR "sr"
#define PYDAW_CONFIGURE_KEY_DR "dr"
#define PYDAW_CONFIGURE_KEY_RR "rr"
#define PYDAW_CONFIGURE_KEY_RI "ri"
#define PYDAW_CONFIGURE_KEY_PLAY "play"
#define PYDAW_CONFIGURE_KEY_REC "rec"
#define PYDAW_CONFIGURE_KEY_STOP "stop"
#define PYDAW_CONFIGURE_KEY_LOOP "loop"
#define PYDAW_CONFIGURE_KEY_TEMPO "tempo"
#define PYDAW_CONFIGURE_KEY_TSIG "tsig"
#define PYDAW_CONFIGURE_KEY_VOL "vol"
#define PYDAW_CONFIGURE_KEY_SOLO "solo"
#define PYDAW_CONFIGURE_KEY_MUTE "mute"
#define PYDAW_CONFIGURE_KEY_CHANGE_INSTRUMENT "ci"

#define PYDAW_LOOP_MODE_OFF 0
#define PYDAW_LOOP_MODE_BAR 1
#define PYDAW_LOOP_MODE_REGION 2
    
//arbitrary, I may change these 3 after evaluating memory use vs. probable item count in a real project
#define PYDAW_MAX_ITEM_COUNT 5000
#define PYDAW_MAX_REGION_COUNT 300
#define PYDAW_MAX_EVENTS_PER_ITEM_COUNT 128
#define PYDAW_MAX_TRACK_COUNT 16
#define PYDAW_REGION_SIZE 8
#define PYDAW_MIDI_NOTE_COUNT 128
    
#include <string.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <ladspa.h>
#include "pydaw_files.h"
#include "pydaw_plugin.h"
    
typedef struct st_pynote
{
    int note;
    int velocity;
    float start;
    float length;    
}t_pynote;

typedef struct st_pycc
{
    int cc_num;
    int cc_val;
    float start;
}t_pycc;

typedef struct st_pyitem
{
    char * name;
    t_pynote * notes[PYDAW_MAX_EVENTS_PER_ITEM_COUNT];
    int note_count;    
    t_pycc * ccs[PYDAW_MAX_EVENTS_PER_ITEM_COUNT];
    int cc_count;
    int resize_factor;
    int note_index[PYDAW_MAX_EVENTS_PER_ITEM_COUNT];
    int cc_index[PYDAW_MAX_EVENTS_PER_ITEM_COUNT];
}t_pyitem;

typedef struct st_pyregion
{
    //t_pyitem * items[PYDAW_MAX_TRACK_COUNT][PYDAW_REGION_SIZE];    
    int item_indexes[PYDAW_MAX_TRACK_COUNT][PYDAW_REGION_SIZE];  //Refers to the index of items in the master item pool
    int item_populated[PYDAW_MAX_TRACK_COUNT][PYDAW_REGION_SIZE];  //1(true) if populated at that index, or 0(false) if not.  Put in place because checking for 0 or NULL in the item doesn't seem to work correctly
    char * name;
}t_pyregion;

typedef struct st_pysong
{
    int region_count;
    t_pyregion * regions[PYDAW_MAX_REGION_COUNT];
    int max_regions;
}t_pysong;

typedef struct st_pytrack
{    
    float volume;
    int solo;
    int mute;
    int plugin_index;
    snd_seq_event_t * event_buffer;
    int event_index;
    t_pydaw_plugin * instrument;
}t_pytrack;

typedef struct st_pydaw_data
{
    int is_initialized;
    float tempo;
    pthread_mutex_t mutex;
    t_pysong * pysong;
    t_pytrack * track_pool[PYDAW_MAX_TRACK_COUNT];
    int track_note_event_indexes[PYDAW_MAX_TRACK_COUNT];
    int track_cc_event_indexes[PYDAW_MAX_TRACK_COUNT];       
    int playback_mode;  //0 == Stop, 1 == Play, 2 == Rec
    int loop_mode;  //0 == Off, 1 == Bar, 2 == Region
    char * project_name;
    char * project_folder;
    char * item_folder;
    char * region_folder;    
    double playback_cursor; //only refers to the fractional position within the current bar.
    double playback_inc;  //the increment per-period to iterate through 1 bar, as determined by sample rate and tempo
    int current_region; //the current region
    int current_bar; //the current bar(0 to 7), within the current region
    int current_bar_start;  //The current bar start in samples
    int current_bar_end;  //The current bar end in samples
    int samples_per_bar;
    float sample_rate;
    int current_sample;  //The sample number of the exact point in the song, 0 == bar0/region0, 44100 == 1 second in at 44.1khz.  Reset to zero on beginning playback        
    int note_offs[PYDAW_MAX_TRACK_COUNT][PYDAW_MIDI_NOTE_COUNT];  //When a note_on event is fired, a sample number of when to release it is stored here
    lo_server_thread serverThread;
    
    char osc_path_tmp[1024];  //TODO:  I could probably get rid of this???
    char * osc_url;
    
    float samples_per_beat;  //The number of samples per beat, for calculating length
    
    t_pyitem * item_pool[PYDAW_MAX_ITEM_COUNT];
    int item_count;
}t_pydaw_data;

void g_pysong_get(t_pydaw_data*, const char*);
t_pytrack * g_pytrack_get();
t_pyregion * g_pyregion_get(t_pydaw_data* a_pydaw, const char*);
void g_pyitem_get(t_pydaw_data* a_pydaw, const char * a_name);
t_pycc * g_pycc_get(char a_cc_num, char a_cc_val, float a_start);
t_pynote * g_pynote_get(char a_note, char a_vel, float a_start, float a_length);
t_pydaw_data * g_pydaw_data_get(float);
int i_get_region_index_from_name(t_pydaw_data * a_pydaw_data, const char * a_name);
void v_open_project(t_pydaw_data*, char*, char*);
void v_set_tempo(t_pydaw_data*,float);
void v_set_playback_cursor(t_pydaw_data * a_pydaw_data, int a_region, int a_bar);
void v_pydaw_parse_configure_message(t_pydaw_data*, const char*, const char*);
int i_pydaw_get_item_index_from_name(t_pydaw_data * a_pydaw_data, const char* a_name);

/*End declarations.  Begin implementations.*/

t_pynote * g_pynote_get(char a_note, char a_vel, float a_start, float a_length)
{
    t_pynote * f_result = (t_pynote*)malloc(sizeof(t_pynote));
    
    f_result->length = a_length;
    f_result->note = a_note;
    f_result->start = a_start;
    f_result->velocity = a_vel;
    
    return f_result;
}

t_pycc * g_pycc_get(char a_cc_num, char a_cc_val, float a_start)
{
    t_pycc * f_result = (t_pycc*)malloc(sizeof(t_pycc));
    
    f_result->cc_num = a_cc_num;
    f_result->cc_val = a_cc_val;
    f_result->start = a_start;
    
    return f_result;
}

void g_pysong_get(t_pydaw_data* a_pydaw, const char * a_name)
{
    char log_buff[200];
    sprintf(log_buff, "\ng_pysong_get\n");
    pydaw_write_log(log_buff);
    t_pysong * f_result = (t_pysong*)malloc(sizeof(t_pysong));
    
    f_result->region_count = 0;
    f_result->max_regions = PYDAW_MAX_REGION_COUNT;
    
    char * f_full_path = (char*)malloc(sizeof(char) * 256);
    strcpy(f_full_path, a_pydaw->project_folder);
    strcat(f_full_path, a_name);
    strcat(f_full_path, ".pysong");
        
    t_2d_char_array * f_current_string = g_get_2d_array_from_file(f_full_path, LMS_LARGE_STRING);    
    free(f_full_path);
    
    int f_i = 0;
    
    while(f_i < PYDAW_MAX_REGION_COUNT)
    {
        f_result->regions[f_i] = 0;
        f_i++;
    }
    
    f_i = 0;
    
    while(f_i < PYDAW_MAX_REGION_COUNT)
    {            
        char * f_pos_char = c_iterate_2d_char_array(f_current_string);
        if(f_current_string->eof)
        {
            break;
        }
        int f_pos = atoi(f_pos_char);        
        char * f_region_char = c_iterate_2d_char_array(f_current_string);
        f_result->regions[f_pos] = g_pyregion_get(a_pydaw, f_region_char);
        free(f_pos_char);
        free(f_region_char);
        f_i++;
    }

    g_free_2d_char_array(f_current_string);
    
    if(a_pydaw->pysong)
    {
        free(a_pydaw->pysong);
    }
    
    a_pydaw->pysong = f_result;
}


int i_pydaw_get_item_index_from_name(t_pydaw_data * a_pydaw_data, const char* a_name)
{
    int f_i = 0;
    
    while(f_i < a_pydaw_data->item_count)
    {
        if(!strcmp(a_name, a_pydaw_data->item_pool[f_i]->name))
        {
            return f_i;
        }
        f_i++;
    }
    
    return -1;
}

t_pyregion * g_pyregion_get(t_pydaw_data* a_pydaw_data, const char * a_name)
{
    char log_buff[200];
    sprintf(log_buff, "\ng_pyregion_get: a_name: \"%s\"\n", a_name);
    pydaw_write_log(log_buff);
    
    t_pyregion * f_result = (t_pyregion*)malloc(sizeof(t_pyregion));    
    
    f_result->name = (char*)malloc(sizeof(char) * 64);
    strcpy(f_result->name, a_name);
    
    int f_i = 0; 
        
    int f_i2 = 0;
    
    while(f_i < PYDAW_MAX_TRACK_COUNT)
    {        
        while(f_i2 < PYDAW_REGION_SIZE)
        {
            f_result->item_populated[f_i][f_i2] = 0;
            f_i2++;
        }
        f_i++;
    }
        
    char * f_full_path = (char*)malloc(sizeof(char) * 256);
    strcpy(f_full_path, a_pydaw_data->region_folder);
    strcat(f_full_path, a_name);
    strcat(f_full_path, ".pyreg");
    
    t_2d_char_array * f_current_string = g_get_2d_array_from_file(f_full_path, LMS_LARGE_STRING);
    
    free(f_full_path);

    f_i = 0;

    while(f_i < 128)
    {            
        char * f_x_char = c_iterate_2d_char_array(f_current_string);
        if(f_current_string->eof)
        {
            break;
        }
        int f_x = atoi(f_x_char);
        free(f_x_char);
        char * f_y_char = c_iterate_2d_char_array(f_current_string);
        int f_y = atoi(f_y_char);
        free(f_y_char);
        char * f_item_name = c_iterate_2d_char_array(f_current_string);
        assert(f_y < PYDAW_MAX_TRACK_COUNT);
        assert(f_x < PYDAW_REGION_SIZE);
        f_result->item_indexes[f_y][f_x] = i_pydaw_get_item_index_from_name(a_pydaw_data, f_item_name);
        assert((f_result->item_indexes[f_y][f_x]) != -1);
        f_result->item_populated[f_y][f_x] = 1;
        sprintf(log_buff, "f_x == %i, f_y = %i\n", f_x, f_y);
        pydaw_write_log(log_buff);
        free(f_item_name);            

        f_i++;
    }

    g_free_2d_char_array(f_current_string);
    
    return f_result;
}

void g_pyitem_get(t_pydaw_data* a_pydaw_data, const char * a_name)
{
    char log_buff[200];
    sprintf(log_buff, "g_pyitem_get: a_name: \"%s\"\n", a_name);
    pydaw_write_log(log_buff);
    
    t_pyitem * f_result = (t_pyitem*)malloc(sizeof(t_pyitem));
    
    f_result->name = (char*)malloc(sizeof(char) * 64);
    strcpy(f_result->name, a_name);
    f_result->cc_count = 0;
    f_result->note_count = 0;
        
    char * f_full_path = (char*)malloc(sizeof(char) * 256);
    strcpy(f_full_path, a_pydaw_data->item_folder);
    strcat(f_full_path, a_name);
    strcat(f_full_path, ".pyitem");
    
    t_2d_char_array * f_current_string = g_get_2d_array_from_file(f_full_path, LMS_LARGE_STRING);
    
    free(f_full_path);

    int f_i = 0;

    while(f_i < 256)
    {   
        char * f_type = c_iterate_2d_char_array(f_current_string);
        
        if(f_current_string->eof)
        {
            break;
        }
        
        char * f_list_pos = c_iterate_2d_char_array(f_current_string);
        
        char * f_start = c_iterate_2d_char_array(f_current_string);
        
        if(!strcmp(f_type, "n"))
        {
            char * f_length = c_iterate_2d_char_array(f_current_string);
            char * f_note_text = c_iterate_2d_char_array(f_current_string);
            free(f_note_text);  //This one is ignored
            char * f_note = c_iterate_2d_char_array(f_current_string);
            char * f_vel = c_iterate_2d_char_array(f_current_string);
            assert((f_result->note_count) < PYDAW_MAX_EVENTS_PER_ITEM_COUNT);
            f_result->notes[(f_result->note_count)] = g_pynote_get(atoi(f_note), atoi(f_vel), atof(f_start), atof(f_length));
            f_result->note_count = (f_result->note_count) + 1;
            
            free(f_length);
            free(f_note);
            free(f_vel);
        }
        else if(!strcmp(f_type, "c"))
        {
            char * f_cc_num = c_iterate_2d_char_array(f_current_string);
            char * f_cc_val = c_iterate_2d_char_array(f_current_string);
            
            f_result->ccs[(f_result->cc_count)] = g_pycc_get(atoi(f_cc_num), atoi(f_cc_val), atof(f_start));
            f_result->cc_count = (f_result->cc_count) + 1;
            
            free(f_cc_num);
            free(f_cc_val);
        }
        else
        {
            sprintf(log_buff, "Invalid event type %s\n", f_type);
            pydaw_write_log(log_buff);
        }
        free(f_list_pos);
        free(f_start);
        free(f_type);
        f_i++;
    }

    g_free_2d_char_array(f_current_string);
    
    int f_item_index = i_pydaw_get_item_index_from_name(a_pydaw_data, a_name);
    
    if(f_item_index < 0)
    {
        a_pydaw_data->item_pool[(a_pydaw_data->item_count)] = f_result;
        a_pydaw_data->item_count = (a_pydaw_data->item_count) + 1;
    }
    else
    {
        free(a_pydaw_data->item_pool[f_item_index]);
        a_pydaw_data->item_pool[f_item_index] = f_result;        
    }
}

t_pytrack * g_pytrack_get()
{
    t_pytrack * f_result = (t_pytrack*)malloc(sizeof(t_pytrack));
    
    f_result->mute = 0;
    f_result->solo = 0;
    f_result->volume = 0.0f;
    f_result->plugin_index = 0;
    f_result->event_buffer = (snd_seq_event_t*)malloc(sizeof(snd_seq_event_t) * 512);
        
    return f_result;
}


void pydaw_osc_error(int num, const char *msg, const char *path)
{
    fprintf(stderr, "PyDAW: liblo server error %d in path %s: %s\n",
	    num, path, msg);
}

t_pydaw_data * g_pydaw_data_get(float a_sample_rate)
{
    t_pydaw_data * f_result = (t_pydaw_data*)malloc(sizeof(t_pydaw_data));
    
    //f_result->mutex = PTHREAD_MUTEX_INITIALIZER;
    pthread_mutex_init(&f_result->mutex, NULL);
    f_result->is_initialized = 0;
    f_result->sample_rate = a_sample_rate;
    f_result->current_sample = 0;
    f_result->loop_mode = 0;
    f_result->item_folder = (char*)malloc(sizeof(char) * 256);
    f_result->project_folder = (char*)malloc(sizeof(char) * 256);
    f_result->region_folder = (char*)malloc(sizeof(char) * 256);
    f_result->project_name = (char*)malloc(sizeof(char) * 256);
    f_result->playback_mode = 0;
    f_result->pysong = 0;
    f_result->item_count = 0;
    
    int f_i = 0;
    
    while(f_i < PYDAW_MAX_TRACK_COUNT)
    {
        f_result->track_pool[f_i] = g_pytrack_get();
        f_result->track_note_event_indexes[f_i] = 0;
        f_result->track_cc_event_indexes[f_i] = 0;
        
        int f_i2 = 0;
        
        while(f_i2 < PYDAW_MIDI_NOTE_COUNT)
        {
            f_result->note_offs[f_i][f_i2] = -1;
            f_i2++;
        }
        
        f_i++;
    }
    
    /* Create OSC thread */    
    char *tmp;
    
    f_result->serverThread = lo_server_thread_new(NULL, pydaw_osc_error);
    snprintf((char *)f_result->osc_path_tmp, 31, "/dssi/pydaw_plugins");
    tmp = lo_server_thread_get_url(f_result->serverThread);
    f_result->osc_url = (char *)malloc(strlen(tmp) + strlen(f_result->osc_path_tmp));
    sprintf(f_result->osc_url, "%s%s", tmp, f_result->osc_path_tmp + 1);    
    free(tmp);
    
    return f_result;
}

void v_pydaw_activate_osc_thread(t_pydaw_data * a_pydaw_data, lo_method_handler osc_message_handler)
{
    lo_server_thread_add_method(a_pydaw_data->serverThread, NULL, NULL, osc_message_handler, NULL);
    lo_server_thread_start(a_pydaw_data->serverThread);
}

void v_open_project(t_pydaw_data* a_pydaw, char* a_project_folder, char* a_name)
{
    char log_buff[200];
    sprintf(log_buff, "\nv_open_project: a_project_folder: %s a_name: \"%s\"\n", a_project_folder, a_name);
    pydaw_write_log(log_buff);
    strcpy(a_pydaw->project_folder, a_project_folder);
    strcat(a_pydaw->project_folder, "/");
    strcpy(a_pydaw->item_folder, a_pydaw->project_folder);
    strcat(a_pydaw->item_folder, "items/");
    sprintf(log_buff, "\na_pydaw->item_folder == %s\n", a_pydaw->item_folder);
    pydaw_write_log(log_buff);
    strcpy(a_pydaw->region_folder, a_pydaw->project_folder);
    strcat(a_pydaw->region_folder, "regions/");
    sprintf(log_buff, "\na_pydaw->region_folder == %s\n\n", a_pydaw->region_folder);
    pydaw_write_log(log_buff);
    strcpy(a_pydaw->project_name, a_name);
    
    t_dir_list * f_item_dir_list = g_get_dir_list(a_pydaw->item_folder);
    
    int f_i = 0;
    
    while(f_i < f_item_dir_list->dir_count)
    {
        t_1d_char_array * f_file_name = c_split_str(f_item_dir_list->dir_list[f_i], '.', 2, LMS_SMALL_STRING);
        g_pyitem_get(a_pydaw, f_file_name->array[0]);
        g_free_1d_char_array(f_file_name);
        f_i++;
    }    
    
    g_pysong_get(a_pydaw, a_name);
    a_pydaw->is_initialized = 1;
}

/* void v_set_playback_mode(t_pydaw_data * a_pydaw_data, 
 * int a_mode, //
 * int a_region, //The region index to start playback on
 * int a_bar) //The bar index (with a_region) to start playback on
 */
void v_set_playback_mode(t_pydaw_data * a_pydaw_data, int a_mode, int a_region, int a_bar)
{
    pthread_mutex_lock(&a_pydaw_data->mutex);
    a_pydaw_data->playback_mode = a_mode;
    
    switch(a_mode)
    {
        case 0:  //stop
            //Initiate some sort of mixer fadeout?
            break;
        case 1:  //play
            a_pydaw_data->current_sample = 0;
            v_set_playback_cursor(a_pydaw_data, a_region, a_bar);
            break;
        case 2:  //record
            a_pydaw_data->current_sample = 0;
            v_set_playback_cursor(a_pydaw_data, a_region, a_bar);
            break;
    }
    
    pthread_mutex_unlock(&a_pydaw_data->mutex);
}

void v_set_playback_cursor(t_pydaw_data * a_pydaw_data, int a_region, int a_bar)
{
    a_pydaw_data->current_bar = a_bar;
    a_pydaw_data->current_region = a_region;
    a_pydaw_data->playback_cursor = 0.0f;
    //TODO:  An  "all notes off" function 
}

void v_set_loop_mode(t_pydaw_data * a_pydaw_data, int a_mode)
{
    pthread_mutex_lock(&a_pydaw_data->mutex);
    a_pydaw_data->loop_mode = a_mode;
    pthread_mutex_unlock(&a_pydaw_data->mutex);
}

void v_set_tempo(t_pydaw_data * a_pydaw_data, float a_tempo)
{
    pthread_mutex_lock(&a_pydaw_data->mutex);
    char log_buff[200];
    a_pydaw_data->tempo = a_tempo;
    a_pydaw_data->playback_inc = ( (1.0f/(a_pydaw_data->sample_rate)) / (60.0f/(a_tempo * 0.25f)) );
    a_pydaw_data->samples_per_beat = (a_pydaw_data->sample_rate)/(a_tempo/60.0f);
    sprintf(log_buff, "a_pydaw_data->playback_inc = %f\n", (a_pydaw_data->playback_inc));
    pydaw_write_log(log_buff);
    pthread_mutex_unlock(&a_pydaw_data->mutex);
}


void v_show_plugin_ui(t_pydaw_data * a_pydaw_data, int a_track_num)
{
    char * filename;
    char oscUrl[256];    
    char * dllName;
    char * label;
            
    switch(a_pydaw_data->track_pool[a_track_num]->plugin_index)
    {
        case 1:
            filename = "/usr/lib/dssi/euphoria/LMS_EUPHORIA_qt";
            dllName = "euphoria.so";
            label = "LMS_EUPHORIA";            
            break;
        case 2:
            filename = "/usr/lib/dssi/ray_v/LMS_RAYV_qt";
            dllName = "ray_v.so";
            label = "LMS_RAYV";            
            break;
    }
    
    char track_number_string[6];
    sprintf(track_number_string, "%i", a_track_num);
    sprintf(oscUrl, "%s/%i", a_pydaw_data->osc_url, a_track_num);
    char instruments_folder[256];
    sprintf(instruments_folder, "%s/instruments", a_pydaw_data->project_folder);
    
    if (fork() == 0) 
    {
        execlp(filename, filename, oscUrl, dllName, label, track_number_string, instruments_folder, track_number_string, NULL);
        perror("exec failed");
        exit(1);  //TODO:  should be getting rid of this???
    }
    
}


void v_set_plugin_index(t_pydaw_data * a_pydaw_data, int a_track_num, int a_index)
{    
    //v_free_pydaw_plugin(a_pydaw_data->track_pool[a_index]->instrument);
    t_pydaw_plugin * f_result;
    
    if(a_index != 0)
    {
        f_result = g_pydaw_plugin_get((int)(a_pydaw_data->sample_rate), a_index);
    }
    pthread_mutex_lock(&a_pydaw_data->mutex);
    a_pydaw_data->track_pool[a_track_num]->instrument = f_result;
    a_pydaw_data->track_pool[a_track_num]->plugin_index = a_index;
    pthread_mutex_unlock(&a_pydaw_data->mutex);
    v_show_plugin_ui(a_pydaw_data, a_track_num);
}

void v_pydaw_parse_configure_message(t_pydaw_data* a_pydaw, const char* a_key, const char* a_value)
{
    char log_buff[200];
    sprintf(log_buff, "v_pydaw_parse_configure_message:  key: \"%s\", value: \"%s\"\n", a_key, a_value);
    pydaw_write_log(log_buff);
    
    if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_SR)) //Save region
    {
        sprintf(log_buff, "v_pydaw_parse_configure_message calling ");
        pydaw_write_log(log_buff);
        g_pyregion_get(a_pydaw, a_value);        
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_SI)) //Save Item
    {
        sprintf(log_buff, "v_pydaw_parse_configure_message calling ");
        pydaw_write_log(log_buff);
        g_pyitem_get(a_pydaw, a_value);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_SS))  //Save Song
    {
        sprintf(log_buff, "v_pydaw_parse_configure_message calling ");
        pydaw_write_log(log_buff);
        g_pysong_get(a_pydaw, a_value);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_PLAY)) //Begin playback
    {
        t_1d_char_array * f_arr = c_split_str(a_value, '|', 2, LMS_SMALL_STRING);
        int f_region = atoi(f_arr->array[0]);
        int f_bar = atoi(f_arr->array[1]);
        v_set_playback_mode(a_pydaw, 1, f_region, f_bar);
        g_free_1d_char_array(f_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_REC)) //Begin recording
    {
        t_1d_char_array * f_arr = c_split_str(a_value, '|', 2, LMS_SMALL_STRING);
        int f_region = atoi(f_arr->array[0]);
        int f_bar = atoi(f_arr->array[1]);
        v_set_playback_mode(a_pydaw, 2, f_region, f_bar);
        g_free_1d_char_array(f_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_STOP)) //Stop playback or recording
    {
        v_set_playback_mode(a_pydaw, 0, -1, -1);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_LOOP)) //Set loop mode
    {
        int f_value = atoi(a_value);
        v_set_loop_mode(a_pydaw, f_value);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_OS)) //Open Song
    {
        t_1d_char_array * f_arr = c_split_str(a_value, '|', 2, LMS_SMALL_STRING);
        v_open_project(a_pydaw, f_arr->array[0], f_arr->array[1]);
        g_free_1d_char_array(f_arr);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_TEMPO)) //Change tempo
    {
        v_set_tempo(a_pydaw, atof(a_value));
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_DI)) //Delete Item
    {
        //Probably won't be implemented anytime soon...
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_DR)) //Delete region
    {
        //Probably won't be implemented anytime soon...
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_RR)) //Rename region
    {
        //Probably won't be implemented anytime soon...
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_RI)) //Rename item
    {
        //Probably won't be implemented anytime soon...
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_SOLO)) //Set track solo
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2, LMS_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_mode = atoi(f_val_arr->array[1]);
        a_pydaw->track_pool[f_track_num]->solo = f_mode;
        g_free_1d_char_array(f_val_arr);
        sprintf(log_buff, "Solo[%i] == %i\n", f_track_num, (a_pydaw->track_pool[f_track_num]->solo));
        pydaw_write_log(log_buff);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_MUTE)) //Set track mute
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2, LMS_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_mode = atoi(f_val_arr->array[1]);
        a_pydaw->track_pool[f_track_num]->mute = f_mode;
        g_free_1d_char_array(f_val_arr);
        sprintf(log_buff, "Mute[%i] == %i\n", f_track_num, (a_pydaw->track_pool[f_track_num]->mute));
        pydaw_write_log(log_buff);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_VOL)) //Set track volume
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2, LMS_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        float f_track_vol = atof(f_val_arr->array[1]);
        a_pydaw->track_pool[f_track_num]->volume = f_track_vol;
        g_free_1d_char_array(f_val_arr);
        sprintf(log_buff, "vol[%i] == %f\n", f_track_num, (a_pydaw->track_pool[f_track_num]->volume));
        pydaw_write_log(log_buff);
    }
    else if(!strcmp(a_key, PYDAW_CONFIGURE_KEY_CHANGE_INSTRUMENT)) //Change the plugin
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2, LMS_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_plugin_index = atof(f_val_arr->array[1]);
        
        v_set_plugin_index(a_pydaw, f_track_num, f_plugin_index);
        
        g_free_1d_char_array(f_val_arr);
    }
    
    else
    {
        sprintf(log_buff, "Unknown configure message key: %s, value %s\n", a_key, a_value);
        pydaw_write_log(log_buff);
    }
}


#ifdef	__cplusplus
}
#endif

#endif	/* PYDAW_H */

