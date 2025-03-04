def check(p, c):
    if c == 'len':
        return len(p) >= 10
    if c == 'upper':
        return any(i.isupper() for i in p)
    if c == 'lower':
        return any(i.islower() for i in p)
    if c == 'digit':
        return any(i.isdigit() for i in p)
    if c == 'symbol':
        return any(i in '@-=' for i in p)
    if c == 'space':
        return ' ' not in p

def count(s, n):
    d = {}
    for i in range(len(s) - n + 1):
        k = s[i:i + n]
        d[k] = d.get(k, 0) + 1
    return d

c = {}
while True:
    u = input()
    if u not in c:
        c[u] = []
    while True:
        p = input()
        if all(check(p, i) for i in ['len', 'upper', 'lower', 'digit', 'symbol', 'space']) and p not in c[u][-3:]:
            c[u].append(p)
            break

with open('fasta_file.txt') as f:
    d = {}
    for l in f.read().split('>')[1:]:
        a = l.split('\n', 1)
        s = a[1].replace('\n', '')
        d[a[0]] = {'mono': count(s, 1), 'di': count(s, 2), 'tri': count(s, 3)}
