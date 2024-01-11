import partcad as pc

if __name__ != "__cqgi__":
    from cq_server.ui import ui, show_object

part = pc.get_part(
    # Part name
    "fastener/screw-buttonhead",
    # Package name
    "standard-metric-cqwarehouse",
)
pc.finalize(part, show_object)
