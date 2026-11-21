"""Assemble walkthrough.html from walkthrough.src.html and the capture (shots/layout.json): the layout constants the
choreography needs, one stacked image per typed state of the search, the register's own figures for page 1, and the
wall of names behind the end card (the register's names, newest first).

Usage: python .impeccable/video/build.py   (after capture.py, from a build whose index is current)"""
import collections, html, io, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
L = json.load(io.open(os.path.join(HERE, 'shots', 'layout.json'), encoding='utf-8'))
src = io.open(os.path.join(HERE, 'walkthrough.src.html'), encoding='utf-8').read()
obs = json.load(io.open(os.path.join(ROOT, 'web', 'public', 'data', 'obituaries.json'), encoding='utf-8'))['obituaries']

# Page 1's figures, said conservatively: notices rounded down to the hundred (shown with a "+"), and the area homes,
# counted as those with more than one notice (a single out-of-area notice doesn't make a home part of the register).
notices = '{:,}'.format(len(obs) // 100 * 100)
homes = str(sum(1 for n in collections.Counter(o.get('homeName') for o in obs if o.get('homeName')).values() if n > 1))

# The wall: rows of names, each row starting at a different offset so no two line up
names = [html.escape(o['name']) for o in sorted(obs, key=lambda o: o.get('sourceDate') or '', reverse=True)]
rows, per = [], 7
for r in range(30):
    chunk = names[r * per:(r + 1) * per]
    rows.append('<div class="nrow" style="left: %dpx; top: %dpx">%s</div>'
                % (-1700 + (r % 3) * 170, r * 78 - 1170, '<b>·</b>'.join(chunk)))

states = ''.join('<img class="state" src="shots/search-%d.png" alt="" style="visibility: hidden">' % i for i in range(len(L['search']['states'])))
out = (src.replace('/*LAYOUT*/', 'const L = ' + json.dumps(L, separators=(',', ':')) + ';')
          .replace('<!--STATES-->', states).replace('<!--NOTICES-->', notices).replace('<!--HOMES-->', homes)
          .replace('<!--NAMES-->', ''.join(rows)))
left = re.findall(r'<!--[A-Z:a-z-]+-->|/\*LAYOUT\*/', out)
if left:
    raise SystemExit('markers left unfilled: %s' % left)
io.open(os.path.join(HERE, 'walkthrough.html'), 'w', encoding='utf-8', newline='\n').write(out)
print('walkthrough.html: %d KB; %s+ notices, %s area homes, %d names on the wall' % (len(out.encode('utf-8')) // 1024, notices, homes, min(len(names), 30 * per)))
