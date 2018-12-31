from BaseHTTPServer import BaseHTTPRequestHandler
import urlparse
import urllib
import re
import glob

import format_sheet

def is_notes(pathcomps):
    return all(re.match(r'[A-G]s?\d', x) for x in pathcomps if x)

def get_notes(pathcomps):
    return [x.replace('s', '#') for x in pathcomps if x]

class GetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        pathcomps = [urllib.unquote(x) for x in parsed_path.path.strip('/').split('/')]
        xml_files = glob.glob('*.xml')
        print(pathcomps)
        
        if len(pathcomps) < 1 or not pathcomps[0]:
            message = self.get_root()
        elif len(pathcomps) == 1:
            # it's a song root
            message = self.get_song_root(pathcomps[0])
        elif len(pathcomps) >= 1 and is_notes(pathcomps[1:]):
            # it's the lyrics file
            message = self.get_lyrics_for_notes(pathcomps[0], get_notes(pathcomps[1:]))
        else:
            message_parts = [
                    'CLIENT VALUES:',
                    'client_address=%s (%s)' % (self.client_address,
                                                self.address_string()),
                    'command=%s' % self.command,
                    'path=%s' % self.path,
                    'real path=%s' % parsed_path.path,
                    'query=%s' % parsed_path.query,
                    'request_version=%s' % self.request_version,
                    '',
                    'SERVER VALUES:',
                    'server_version=%s' % self.server_version,
                    'sys_version=%s' % self.sys_version,
                    'protocol_version=%s' % self.protocol_version,
                    '',
                    'HEADERS RECEIVED:',
                    ]
            for name, value in sorted(self.headers.items()):
                message_parts.append('%s=%s' % (name, value.rstrip()))
            message_parts.append('')
            message = '\r\n'.join(message_parts)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(message)
        return

    def get_root(self):
        xml_files = glob.glob('*.xml')
        song_tmpl = '''<li><a href="/{file}/">{file}</a></li>'''
        songs = '\n'.join(song_tmpl.format(file=x) for x in xml_files)
        return open('root.html').read().format(songs=songs)

    def get_song_root(self, xml):
        from collections import Counter
        counts = Counter()
        chords = format_sheet.parse_to_chords(xml)
        for c in chords:
            if c.lyric:
                counts.update(c.notes)

        buttons = '\n'.join(
            '<a onclick="toggle(\'{notename}\')"><li id="{notename}"><h2>{note}</h2><h3>({count})</h3></li></a>'
            .format(note=note, count=count, notename=note.replace('#', 's'))
            for (note, count) in counts.most_common())

        return open('song_root.html').read().format(song_title=xml, buttons=buttons)

    def get_lyrics_for_notes(self, xml, notes):
        print(notes)
        chords = format_sheet.parse_to_chords(xml)
        notechars = dict(zip(notes, '1234'))
        lyric_line = '''<p class="lyric">{lyrics}</p>'''
        lyric = '''<span class='{classes}'>{lyric}</span>'''
        legend = " ".join (lyric.format(lyric=note, classes='l{}'.format(c))
                  for (note,c) in zip(notes, '1234'))
        lines = format_sheet.create_lyric_lines(chords, notechars)
        result = ''
        for line in lines:

            out_lyrics = []
            for (l, b) in zip(line.lyrics, line.bells):
                classes = ' '.join('l{}'.format(s) for s in '1234' if s in b)
                out_lyrics.append(lyric.format(lyric=l, classes=classes))
            out_linestr = lyric_line.format(lyrics='\n'.join(out_lyrics))
            result = result + out_linestr

        return open('lyrics.html').read().format(song_title=xml, legend=legend, lyrics=result)

if __name__ == '__main__':
    from BaseHTTPServer import HTTPServer
    print("Loading song xml")
    server = HTTPServer(('192.168.3.25', 8000), GetHandler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()

