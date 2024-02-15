import build123d as b3d
import partcad as pc

part = pc.get_part_build123d(
    # Part name
    "fastener/screw-buttonhead",
    # Package name
    "standard-metric-cqwarehouse",
)

show_object(part)
