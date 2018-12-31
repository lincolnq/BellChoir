# coding: UTF-8
import xml.etree.ElementTree as ET

class Chord:
    def __init__(self, notes):
        self.notes = notes
        self.lyric = None
    
    def __repr__(self):
        return "{} {}".format(self.lyric, self.notes)

def alter_pitch(alter, step):
    STEPS = 'CDEFGAB'
    if alter == 0:
        return step
    if alter == 1:
        return step + '#'
    if alter == -1:
        return STEPS[STEPS.index(step) - 1] + '#'
    else:
        assert False, "bad alter"

def to_notestr(note_elem):

    estep = note_elem.find('./pitch/step')
    alter = note_elem.find('./pitch/alter')
    octave = note_elem.find('./pitch/octave')

    if estep is None or octave is None:
        return None

    step = estep.text
    if alter is not None:
        step = alter_pitch(int(alter.text), step)

    return '{}{}'.format(step, octave.text)

def parse_to_chords(notesfile):
    tree = ET.parse(notesfile)
    root = tree.getroot()

    notes = root.findall('./part/measure/note')
    results = []

    for n in notes:
        pitch = to_notestr(n)
        if not pitch:
            continue
        ischord = n.find('./chord')
        lyric = n.find('./lyric/text')
        lyric_syllabic = n.find('./lyric/syllabic')

        if ischord is None:
            curchord = Chord(notes=[pitch])
            results.append(curchord)
        else:
            curchord = results[-1]
            curchord.notes.append(pitch)

        if lyric is not None:
            curchord.lyric = lyric.text
            if lyric_syllabic is not None and lyric_syllabic.text.lower() == 'begin':
                curchord.lyric = curchord.lyric + '-'

    return results

class Line:
    def __init__(self):
        self.lyrics = []
        self.bells = []


def create_lyric_lines(chords, note_chars):
    lines = [Line()]

    for c in chords:
        if not c.lyric:
            continue
        
        if c.lyric[0].isupper():
            lines.append(Line())

        line = lines[-1]
        line.lyrics.append(c.lyric)
        bells = ''.join(note_chars[x] for x in c.notes if x in note_chars)
        line.bells.append(bells + ' ' * (len(c.lyric) - len(bells)))

    return lines


def main():
    import sys
    assert len(sys.argv) >= 3, "Usage: format_sheet <xml> <note1> <note2>"
    notes_of_interest = sys.argv[2:]

    chords = parse_to_chords(sys.argv[1])
    print(chords)

    ARROWS = u"↖↗↘↙"
    note_chars = dict(zip(notes_of_interest, ARROWS))

    print(u"\n".join(u"{} = {}".format(n,c) for (n, c) in note_chars.items()))

    # now print the lyrics
    lines = create_lyric_lines(chords, note_chars)

    for line in lines:
        lyrics_str = ' '.join(line.lyrics)
        bells_str = ' '.join(line.bells)
        print(u'{}\n{}'.format(lyrics_str, bells_str))

if __name__ == '__main__':
    main()
