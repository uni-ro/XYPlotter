import subprocess

step = 2.5

rangeX1 = 5
rangeY1 = 5

rangeRX = 5
rangeRY = 5

rangeRot = 5

rangeLarge = 2
rangeSweep = 2

rangeX2 = 5
rangeY2 = 5


def range2(min, max, step):
    length = int((max - min)/step)

    values = []
    value = min

    for v in range(length):
        values.append(value)
        value += step

    return values


for a in range2(0, rangeX1/2 + step, step):
    for b in range2(-rangeX2/2, rangeX2/2 + step, step):
        for c in range2(-rangeRX/2, rangeRX/2 + step, step):
            for d in range2(-rangeRY/2, rangeRY/2 + step, step):
                for e in range2(-rangeRot/2, rangeRot/2 + step, step):
                    for f in range(rangeLarge):
                        for g in range(rangeSweep):
                            for h in range2(-rangeX2/2, rangeX2/2 + step, step):
                                for i in range2(-rangeY2/2, rangeY2/2 + step, step):
                                    subprocess.run(['python3', 'pointList.py', 'test', str(a), str(b), str(c), str(d), str(e), str(f), str(g), str(h), str(i)])

