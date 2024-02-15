import cadquery as cq
import partcad as pc

part = pc.get_part_cadquery(
    # Part name
    "fastener/screw-buttonhead",
    # Package name
    "standard-metric-cqwarehouse",
)

show_object(part)
