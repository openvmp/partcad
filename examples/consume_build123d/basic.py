import build123d as b3d
import partcad as pc

part = pc.get_part(
    # Part name
    "fastener/screw-buttonhead",
    # Package name
    "standard-metric-cqwarehouse",
).get_build123d()

show_object(part)
