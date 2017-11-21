import json
def color_map(N=256):
    def bitget(byteval, idx):
        return ((byteval & (1 << idx)) != 0)
    cmap = []
    for i in range(N):
        r = g = b = 0
        c = i
        for j in range(8):
            r = r | (bitget(c, 0) << 7-j)
            g = g | (bitget(c, 1) << 7-j)
            b = b | (bitget(c, 2) << 7-j)
            c = c >> 3
        cmap.append([r, g, b])
    return cmap

classes = ['Eraser', 'TZ', 'SCJ', 'CIS', 'CIGN', 'PUN', 'MOS', 'AE']

def getcolormap():
    cmap = color_map()
    colormap = {}
    cmap = cmap[1:len(cmap)]
    for label, color in zip(classes, cmap):
        colormap[label] = color
    return colormap

COLORMAP = getcolormap()

out = json.dumps(COLORMAP)

print(out)