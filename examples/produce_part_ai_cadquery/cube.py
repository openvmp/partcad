import cadquery as cq

# Define the cube's length
length = 10

# Create a new cube with the specified length
cube = cq.Workplane("XY").box(length, length, length)

# Display the cube
show_object(cube)
