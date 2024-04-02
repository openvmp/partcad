import math
import cadquery as cq

length = 10

def create_tetrahedron(length):
    height = math.sqrt(2/3) * length
    radius = math.sqrt(6)/3 * length
    
    v0 = cq.Vector(0, 0, 0)
    v1 = cq.Vector(length, 0, 0)
    v2 = cq.Vector(length/2, height, 0)
    v3 = cq.Vector(length/2, height/3, radius)
    
    tetrahedron = cq.Workplane("XY").polyline([v0, v1, v2, v0]) \
        .polyline([v0, v2, v3, v0]) \
        .polyline([v1, v3, v2, v1]) \
        .polyline([v1, v0, v3, v1]) \
        .close()

    return tetrahedron

tetrahedron = create_tetrahedron(length)
show_object(tetrahedron)