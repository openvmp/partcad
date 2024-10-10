import cadquery as cq

sk1 = (
    cq.Sketch()
    .rect(3.0, 4.0)
    .push([(0, 0.75), (0, -0.75)])
    .regularPolygon(0.5, 6, 90, mode="s")
)

result = cq.Workplane("front").placeSketch(sk1)
show_object(result)
