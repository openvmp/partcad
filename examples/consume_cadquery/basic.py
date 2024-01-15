import cadquery as cq
import partcad as pc

part = pc.get_part(
    # Part name
    "fastener/screw-buttonhead",
    # Package name
    "standard-metric-cqwarehouse",
).get_cadquery()

show_object(part)
