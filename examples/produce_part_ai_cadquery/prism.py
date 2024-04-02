import cadquery as cq

# Define the hexagonal prism
length = 10
hex_prism = cq.Workplane("XY").polygon(6, length).extrude(length)

show_object(hex_prism)