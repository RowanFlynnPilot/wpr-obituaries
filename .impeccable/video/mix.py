"""Score the rendered walkthrough: the music bed (audio/music.mp3, a reverent piano-and-strings track generated for this
video, which swells under pages 5-6 and resolves to its last chord over the end card) and a soft newsprint page turn
on every page turn, mixed and loudness-normalized, then muxed onto both silent renders. The silent renders stay too:
feeds that autoplay muted, and anywhere music would be out of place.

Usage: python .impeccable/video/mix.py   (after render.mjs has written WPR-Obituaries-walkthrough-silent.mp4 and
the -silent-for-text copy)"""
import os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, 'audio')
DURATION = 62.0
TURNS = [5.4, 13.4, 21.4, 29.4, 37.4, 45.0, 53.2]      # page turns in the composition (PAGES)
TURN_GAIN = 1.4                # a page turned by hand under the piano, not a swoosh
BED_GAIN = 0.9


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise SystemExit(p.stderr[-2000:])


inputs = ['-i', os.path.join(A, 'music.mp3')]
filters = ['[0:a]atrim=0:%s,asetpts=PTS-STARTPTS,volume=%s,afade=t=in:d=0.3,afade=t=out:st=%.1f:d=1.8,apad=whole_dur=%s[bed]'
           % (DURATION, BED_GAIN, DURATION - 1.8, DURATION)]
labels = ['[bed]']
for i, t in enumerate(TURNS):
    inputs += ['-i', os.path.join(A, 'turn2.mp3')]       # turn1 came back nearly silent (-31 dB peak); one take serves
    ms = int(t * 1000)
    filters.append('[%d:a]volume=%s,adelay=%d|%d[s%d]' % (i + 1, TURN_GAIN, ms, ms, i))
    labels.append('[s%d]' % i)
filters.append('%samix=inputs=%d:normalize=0:duration=first,loudnorm=I=-16:TP=-1.5:LRA=11,atrim=0:%s[mix]'
               % (''.join(labels), len(labels), DURATION))
mix = os.path.join(A, 'mix.m4a')
run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(filters), '-map', '[mix]',
     '-ar', '48000', '-c:a', 'aac', '-b:a', '256k', mix])

for silent, out, rate in (('WPR-Obituaries-walkthrough-silent.mp4', 'WPR-Obituaries-walkthrough.mp4', '192k'),
                          ('WPR-Obituaries-walkthrough-silent-for-text.mp4', 'WPR-Obituaries-walkthrough-for-text.mp4', '64k')):
    run(['ffmpeg', '-y', '-v', 'error', '-i', os.path.join(HERE, silent), '-i', mix, '-map', '0:v', '-map', '1:a',
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', rate, '-shortest', '-movflags', '+faststart', os.path.join(HERE, out)])
    print('%s: %.1f MB' % (out, os.path.getsize(os.path.join(HERE, out)) / 1e6))
