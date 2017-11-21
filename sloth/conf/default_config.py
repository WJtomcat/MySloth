# This is sloth's default configuration.
#
# The configuration file is a simple python module with module-level
# variables.  This module contains the default values for sloth's
# configuration variables.
#
# In all cases in the configuration where a python callable (such as a
# function, class constructor, etc.) is expected, it is equally possible
# to specify a module path (as string) pointing to such a python callable.
# It will then be automatically imported.

# LABELS
#
# List/tuple of dictionaries that defines the label classes
# that are handled by sloth.  For each label, there should
# be one dictionary that contains the following keys:
#
#   - 'item' : Visualization item for this label. This can be
#              any python callable or a module path string
#              implementing the visualization item interface.
#
#   - 'inserter' : (optional) Item inserter for this label.
#                  If the user selects to insert a new label of this class
#                  the inserter is responsible to actually
#                  capture the users mouse actions and insert
#                  a new label into the annotation model.
#
#   - 'hotkey' : (optional) A keyboard shortcut starting
#                the insertion of a new label of this class.
#
#   - 'attributes' : (optional) A dictionary that defines the
#                    keys and possible values of this label
#                    class.
#
#   - 'text' : (optional) A label for the item's GUI button.
# LABELS = (
#     {
#         'attributes': {
#             'class':    'TZ',
#         },
#         'inserter': 'sloth.items.FreehandItemInserter',
#         'item':     'sloth.items.PolygonItem',
#         'hotkey':   't',
#         'text':     'TZ(t)',
#     },
#     {
#         'attributes': {
#             'class':    'SCJ',
#         },
#         'inserter': 'sloth.items.FreehandItemInserter',
#         'item':     'sloth.items.PolygonItem',
#         'hotkey':   's',
#         'text':     'SCJ(s)',
#     },
#     {
#         'attributes': {
#             'class':    'CIS',
#         },
#         'inserter': 'sloth.items.FreehandItemInserter',
#         'item':     'sloth.items.PolygonItem',
#         'hotkey':   'c',
#         'text':     'CIS(c)',
#     },
#     {
#         'attributes': {
#             'class':    'CIGN',
#         },
#         'inserter': 'sloth.items.FreehandItemInserter',
#         'item':     'sloth.items.PolygonItem',
#         'hotkey':   'g',
#         'text':     'CIGN(g)',
#     },
#     {
#         'attributes': {
#             'class':    'PUN',
#         },
#         'inserter': 'sloth.items.FreehandItemInserter',
#         'item':     'sloth.items.PolygonItem',
#         'hotkey':   'p',
#         'text':     'PUN(p)',
#     },
#     {
#         'attributes': {
#             'class':    'MOS',
#         },
#         'inserter': 'sloth.items.FreehandItemInserter',
#         'item':     'sloth.items.PolygonItem',
#         'hotkey':   'm',
#         'text':     'MOS(m)',
#     },
#     {
#         'attributes': {
#             'class':    'AE',
#         },
#         'inserter': 'sloth.items.FreehandItemInserter',
#         'item':     'sloth.items.PolygonItem',
#         'hotkey':   'a',
#         'text':     'AE(a)',
#     },
#     {
#         'attributes': {
#             'class':    'Eraser',
#         },
#         'inserter': 'sloth.items.FreehandEraser',
#         'hotkey':   'Ctrl+e',
#         'text':     'Eraser(e)',
#     },
# )

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




# HOTKEYS
#
# Defines the keyboard shortcuts.  Each hotkey is defined by a tuple
# with at least 2 entries, where the first entry is the hotkey (sequence),
# and the second entry is the function that is called.  The function
# should expect a single parameter, the labeltool object.  The optional
# third entry -- if present -- is expected to be a string describing the
# action.

HOTKEYS = (
    ('Space',     [lambda lt: lt.currentImage().confirmAll(),
                   lambda lt: lt.currentImage().setUnlabeled(False),
                   lambda lt: lt.gotoNext()
                  ],                                         'Mark image as labeled/confirmed and go to next'),
    ('Backspace', lambda lt: lt.gotoPrevious(),              'Previous image/frame'),
    ('PgDown',    lambda lt: lt.gotoNext(),                  'Next image/frame'),
    ('PgUp',      lambda lt: lt.gotoPrevious(),              'Previous image/frame'),
    ('Tab',       lambda lt: lt.selectNextAnnotation(),      'Select next annotation'),
    ('Shift+Tab', lambda lt: lt.selectPreviousAnnotation(),  'Select previous annotation'),
    ('Ctrl+f',    lambda lt: lt.view().fitInView(),          'Fit current image/frame into window'),
    ('Del',       lambda lt: lt.deleteSelectedAnnotations(), 'Delete selected annotations'),
    ('ESC',       lambda lt: lt.exitInsertMode(),            'Exit insert mode'),
    ('Shift+l',   lambda lt: lt.currentImage().setUnlabeled(False), 'Mark current image as labeled'),
    ('Shift+c',   lambda lt: lt.currentImage().confirmAll(), 'Mark all annotations in image as confirmed'),
)

