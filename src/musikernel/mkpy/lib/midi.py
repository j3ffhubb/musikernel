from mkpy.lib.util import MidiEvent
from mkpy.vendor import mido

def load_midi_file(a_file):
    f_midi_text_arr = mido.MidiFile(str(a_file))
    #First fix the lengths of events that have note-off events
    f_note_on_dict = {}
    f_item_list = []
    f_pos = 0
    f_sec_per_beat = 0.5
    for f_ev in f_midi_text_arr:
        if f_ev.type == "set_tempo":
            f_sec_per_beat = f_ev.tempo / 1000000.0
        elif f_ev.type == "note_off" or (
        f_ev.type == "note_on" and f_ev.velocity == 0):
            f_tuple = (f_ev.channel, f_ev.note)
            if f_tuple in f_note_on_dict:
                f_event = f_note_on_dict[f_tuple]
                f_event.length = f_pos - f_event.start_beat
                f_item_list.append(f_event)
                f_note_on_dict.pop(f_tuple)
            else:
                print(
                    "Error, note-off event does not correspond to a "
                    "note-on event, ignoring event:\n{}".format(f_ev)
                )
        elif f_ev.type == "note_on":
            f_event = MidiEvent(f_ev, f_pos)
            f_tuple = (f_ev.channel, f_ev.note)
            if f_tuple in f_note_on_dict:
                f_note_on_dict[f_tuple].length = f_pos - f_event.start_beat
            f_note_on_dict[f_tuple] = f_event
        else:
            print("Ignoring event: {}".format(f_ev))
        f_pos += f_ev.time / f_sec_per_beat

    f_item_list.sort()
    return f_item_list

