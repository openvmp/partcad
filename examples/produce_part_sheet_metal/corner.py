# The other part this package folds from the same blank: one bend, in the
# middle, so the strip comes out as an L with two equal legs.
#
# It is the same script as 'bracket.py' with one fewer corner in it, and that is
# the point of the pair: what makes the two parts different is which bend lines
# the instructions select out of the one drawing, not two drawings.

from math import radians, tan

import build123d as bd

THICKNESS = 2.0  # the sheet the blank is cut from
INNER_RADIUS = 2.0  # what 'radius' says against the bend line
BEND_ANGLE = 90.0  # ...and what 'angle' says
WIDTH = 40.0  # across the blank
FLAT_LEG = 60.0  # from each edge of the blank to the bend line

# The neutral axis sits at mid-thickness, so the flat length the bend takes up
# is its arc there, while a sharp corner would take up the two tangent lengths
# instead. See 'bracket.py', which says the whole of it.
NEUTRAL = INNER_RADIUS + THICKNESS / 2
SETBACK = NEUTRAL * tan(radians(BEND_ANGLE) / 2) - NEUTRAL * radians(BEND_ANGLE) / 2
LEG = FLAT_LEG + SETBACK

with bd.BuildPart() as result:
    with bd.BuildLine(bd.Plane.XZ) as centreline:
        bd.Polyline((0, 0), (LEG, 0), (LEG, LEG))
        # The corner itself, named by where it is: the two vertices of the
        # vertical leg share an X, so sorting on that would pick between them
        # by whatever order they came out in - and one of the two is the free
        # end of the strip, which is not a bend.
        corner = centreline.vertices().sort_by_distance(bd.Vector(LEG, 0, 0))[0]
        bd.fillet([corner], radius=NEUTRAL)
    with bd.BuildSketch(bd.Plane.YZ):
        bd.Rectangle(WIDTH, THICKNESS)
    bd.sweep()

if "show_object" in locals():
    show_object(result.part.wrapped, name="corner")
