# Original code taken from https://gist.github.com/SDI8/3137ee70649e4901913c7c8e6b534ec8

"""
MIT License
Copyright (c) 2022 Simon Dibbern
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import copyreg
from io import BytesIO

import cadquery as cq
import OCP


def _inflate_shape(data: bytes):
    with BytesIO(data) as bio:
        return cq.Shape.importBrep(bio)


def _reduce_shape(shape: cq.Shape):
    with BytesIO() as stream:
        shape.exportBrep(stream)
        return _inflate_shape, (stream.getvalue(),)


def _inflate_transform(*values: float):
    trsf = OCP.gp.gp_Trsf()
    trsf.SetValues(*values)
    return trsf


def _reduce_transform(transform: OCP.gp.gp_Trsf):
    return _inflate_transform, tuple(
        transform.Value(i, j) for i in range(1, 4) for j in range(1, 5)
    )


def _inflate_Gtransform(*values):
    gtrsf = OCP.gp.gp_GTrsf(values[0], values[1])
    return gtrsf


def _reduce_Gtransform(transform: OCP.gp.gp_GTrsf):
    return _inflate_Gtransform, tuple(
        [
            transform.VectorialPart(),
            transform.TranslationPart(),
        ]
    )


def _inflate_mat(*values):
    trsf = OCP.gp.gp_Mat(values[0], values[1], values[2])
    return trsf


def _reduce_mat(mat: OCP.gp.gp_Mat):
    return _inflate_mat, (
        mat.Column(1),
        mat.Column(2),
        mat.Column(3),
    )


def _inflate_compound(data: bytes):
    with BytesIO(data) as bio:
        shape = OCP.TopoDS.TopoDS_Compound()
        builder = OCP.BRep.BRep_Builder()
        OCP.BRepTools.BRepTools.Read_s(shape, bio, builder)
        return shape


def _reduce_compound(compound: OCP.TopoDS.TopoDS_Compound):
    with BytesIO() as stream:
        OCP.BRepTools.BRepTools.Write_s(compound, stream)
        return _inflate_compound, (stream.getvalue(),)


def _inflate_solid(data: bytes):
    with BytesIO(data) as bio:
        shape = OCP.TopoDS.TopoDS_Solid()
        builder = OCP.BRep.BRep_Builder()
        OCP.BRepTools.BRepTools.Read_s(shape, bio, builder)
        return shape


def _reduce_solid(compound: OCP.TopoDS.TopoDS_Solid):
    with BytesIO() as stream:
        OCP.BRepTools.BRepTools.Write_s(compound, stream)
        return _inflate_solid, (stream.getvalue(),)


def _inflate_ax3(*values: float):
    ax3 = OCP.gp.gp_Ax3()
    ax3.SetLocation(values[0])
    ax3.SetDirection(values[1])
    return ax3


def _reduce_ax3(ax3: OCP.gp.gp_Ax3):
    return _inflate_ax3, (ax3.Location(), ax3.Direction())


def _inflate_pnt(*values: float):
    pnt = OCP.gp.gp_Pnt(values[0], values[1], values[2])
    return pnt


def _reduce_pnt(pnt: OCP.gp.gp_Pnt):
    return _inflate_pnt, (pnt.X(), pnt.Y(), pnt.Z())


def _inflate_dir(*values: float):
    dir = OCP.gp.gp_Dir(values[0], values[1], values[2])
    return dir


def _reduce_dir(dir: OCP.gp.gp_Dir):
    return _inflate_dir, (dir.X(), dir.Y(), dir.Z())


def _inflate_xyz(*values: float):
    dir = OCP.gp.gp_XYZ(values[0], values[1], values[2])
    return dir


def _reduce_xyz(dir: OCP.gp.gp_XYZ):
    return _inflate_xyz, (dir.X(), dir.Y(), dir.Z())


def register():
    """
    Registers pickle support functions for common CadQuery and OCCT objects.
    """

    for cls in (
        cq.Edge,
        cq.Compound,
        cq.Shell,
        cq.Face,
        cq.Solid,
        cq.Vertex,
        cq.Wire,
    ):
        copyreg.pickle(cls, _reduce_shape)

    copyreg.pickle(OCP.gp.gp_Pnt, _reduce_pnt)
    copyreg.pickle(OCP.gp.gp_Dir, _reduce_dir)
    copyreg.pickle(OCP.gp.gp_Mat, _reduce_mat)
    copyreg.pickle(OCP.gp.gp_XYZ, _reduce_xyz)

    copyreg.pickle(OCP.gp.gp_Ax3, _reduce_ax3)

    copyreg.pickle(cq.Vector, lambda vec: (cq.Vector, vec.toTuple()))
    copyreg.pickle(OCP.gp.gp_Trsf, _reduce_transform)
    copyreg.pickle(OCP.gp.gp_GTrsf, _reduce_Gtransform)
    copyreg.pickle(
        cq.Location, lambda loc: (cq.Location, (loc.wrapped.Transformation(),))
    )
    copyreg.pickle(OCP.TopoDS.TopoDS_Compound, _reduce_compound)
    copyreg.pickle(OCP.TopoDS.TopoDS_Solid, _reduce_solid)
