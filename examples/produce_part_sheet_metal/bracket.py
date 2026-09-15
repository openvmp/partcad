# The bracket this package declares as 'sheet_metal': the blank, bent.
#
# Modelled from the very numbers the drawing states - the flat pattern's leg and
# web lengths, and the angle and inner radius written against each bend line -
# because that is the relationship the declaration describes. PartCAD does not
# bend the blank itself yet, so this script is where the two are kept in step.
#
# A piece of sheet is a cross-section carried along a line, so that is how it is
# built: the centreline of the bent profile, filleted where it turns, with the
# section of the strip swept along it. The part comes out with exactly the
# volume of the blank, because that is what bending does to a piece of metal.

from math import radians, tan

import build123d as bd

THICKNESS = 2.0  # the sheet the blank is cut from
INNER_RADIUS = 2.0  # what 'radius' says against each bend line
BEND_ANGLE = 90.0  # ...and what 'angle' says
WIDTH = 40.0  # across the blank
FLAT_LEG = 30.0  # from the edge of the blank to the nearer bend line
FLAT_WEB = 60.0  # between the two bend lines

# The neutral axis sits at mid-thickness, so the flat length a bend takes up is
# its arc there, while a sharp corner would take up the two tangent lengths
# instead. Sharing that difference between the segments either side is what
# turns the flat pattern's dimensions into the sharp-cornered centreline below -
# and is why the centreline comes back out 120mm long, which is the blank.
NEUTRAL = INNER_RADIUS + THICKNESS / 2
SETBACK = NEUTRAL * tan(radians(BEND_ANGLE) / 2) - NEUTRAL * radians(BEND_ANGLE) / 2
LEG = FLAT_LEG + SETBACK
WEB = FLAT_WEB + 2 * SETBACK

with bd.BuildPart() as result:
    with bd.BuildLine(bd.Plane.XZ) as centreline:
        bd.Polyline((0, 0), (LEG, 0), (LEG, WEB), (LEG + LEG, WEB))
        # The two corners of the Z, and only those: the ends of the strip are
        # where the metal stops, not where it turns.
        bd.fillet(centreline.vertices().sort_by(bd.Axis.X)[1:-1], radius=NEUTRAL)
    with bd.BuildSketch(bd.Plane.YZ):
        bd.Rectangle(WIDTH, THICKNESS)
    bd.sweep()

if "show_object" in locals():
    show_object(result.part.wrapped, name="bracket")
