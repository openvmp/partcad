import partcad as pc

part = pc.get_part(
    # Part name
    "fastener/hexhead-iso4014",
    # Package name
    "pc-std-metric-cqwarehouse",
)
part.show()
