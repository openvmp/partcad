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

# Also influenced by https://github.com/gumyr/build123d/blob/dev/src/build123d/persistence.py

"""
build123d pickle support

name: persistence.py
by:   Jojain & bernhard-42
date: September 8th, 2023

desc:
    This python module enables build123d objects to be pickled.

license:

    Copyright 2023 Jojain & bernhard-42

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""

import copyreg
from io import BytesIO
from typing import Any

import cadquery as cq
import OCP
from OCP.TopAbs import TopAbs_Orientation, TopAbs_ShapeEnum
from OCP.BinTools import BinTools
from OCP.gp import gp_Quaternion, gp_Trsf, gp_Vec
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import (
    TopoDS,
    TopoDS_Compound,
    TopoDS_CompSolid,
    TopoDS_Edge,
    TopoDS_Face,
    TopoDS_Shape,
    TopoDS_Shell,
    TopoDS_Solid,
    TopoDS_Vertex,
    TopoDS_Wire,
)

import OCP.TopAbs as ta

downcast_LUT = {
    ta.TopAbs_VERTEX: TopoDS.Vertex_s,
    ta.TopAbs_EDGE: TopoDS.Edge_s,
    ta.TopAbs_WIRE: TopoDS.Wire_s,
    ta.TopAbs_FACE: TopoDS.Face_s,
    ta.TopAbs_SHELL: TopoDS.Shell_s,
    ta.TopAbs_SOLID: TopoDS.Solid_s,
    ta.TopAbs_COMPOUND: TopoDS.Compound_s,
    ta.TopAbs_COMPSOLID: TopoDS.CompSolid_s,
}


def shapetype(obj: TopoDS_Shape) -> TopAbs_ShapeEnum:
    """Return TopoDS_Shape's TopAbs_ShapeEnum"""
    if obj.IsNull():
        raise ValueError("Null TopoDS_Shape object")

    return obj.ShapeType()


def downcast(obj: TopoDS_Shape) -> TopoDS_Shape:
    """Downcasts a TopoDS object to suitable specialized type

    Args:
      obj: TopoDS_Shape:

    Returns:

    """

    f_downcast: Any = downcast_LUT[shapetype(obj)]
    return_value = f_downcast(obj)

    return return_value


def _inflate_shape(data: bytes):
    with BytesIO(data) as bio:
        return cq.Shape.importBrep(bio)


def _reduce_shape(shape: cq.Shape):
    with BytesIO() as stream:
        shape.exportBrep(stream)
        return _inflate_shape, (stream.getvalue(),)


def _inflate_topods(data: bytes):
    with BytesIO(data) as bio:
        shape = TopoDS_Shape()
        builder = OCP.BRep.BRep_Builder()
        OCP.BRepTools.BRepTools.Read_s(shape, bio, builder)
        return downcast(shape)


def _reduce_topods(shape):
    with BytesIO() as bio:
        OCP.BRepTools.BRepTools.Write_s(shape, bio)
        return _inflate_topods, (bio.getvalue(),)


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


def _inflate_ax1(*values: float):
    ax1 = OCP.gp.gp_Ax1(values[0], values[1])
    return ax1


def _reduce_ax1(ax1: OCP.gp.gp_Ax1):
    return _inflate_ax1, (
        ax1.Location(),
        ax1.Direction(),
    )


def _inflate_ax3(*values: float):
    ax3 = OCP.gp.gp_Ax3(values[0], values[1], values[2])
    ax3.SetYDirection(values[3])
    return ax3


def _reduce_ax3(ax3: OCP.gp.gp_Ax3):
    return _inflate_ax3, (
        ax3.Location(),
        ax3.Direction(),
        ax3.XDirection(),
        ax3.YDirection(),
    )


def _inflate_pln(*values: float):
    ax3 = OCP.gp.gp_Ax3(values[0], values[1], values[2])
    ax3.SetYDirection(values[3])
    pln = OCP.gp.gp_Pln(ax3)
    return pln


def _reduce_pln(pln: OCP.gp.gp_Pln):
    ax3 = pln.Position()
    return _inflate_pln, (
        ax3.Location(),
        ax3.Direction(),
        ax3.XDirection(),
        ax3.YDirection(),
    )


def _inflate_pnt(*values: float):
    pnt = OCP.gp.gp_Pnt(values[0], values[1], values[2])
    return pnt


def _reduce_pnt(pnt: OCP.gp.gp_Pnt):
    return _inflate_pnt, (pnt.X(), pnt.Y(), pnt.Z())


def _inflate_vec(*values: float):
    pnt = OCP.gp.gp_Vec(values[0], values[1], values[2])
    return pnt


def _reduce_vec(pnt: OCP.gp.gp_Vec):
    return _inflate_vec, (pnt.X(), pnt.Y(), pnt.Z())


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
    copyreg.pickle(OCP.gp.gp_Vec, _reduce_vec)
    copyreg.pickle(OCP.gp.gp_Dir, _reduce_dir)
    copyreg.pickle(OCP.gp.gp_Mat, _reduce_mat)
    copyreg.pickle(OCP.gp.gp_XYZ, _reduce_xyz)

    copyreg.pickle(OCP.gp.gp_Ax1, _reduce_ax1)
    copyreg.pickle(OCP.gp.gp_Ax3, _reduce_ax3)
    copyreg.pickle(OCP.gp.gp_Pln, _reduce_pln)

    copyreg.pickle(cq.Vector, lambda vec: (cq.Vector, vec.toTuple()))
    copyreg.pickle(OCP.gp.gp_Trsf, _reduce_transform)
    copyreg.pickle(OCP.gp.gp_GTrsf, _reduce_Gtransform)
    copyreg.pickle(
        cq.Location, lambda loc: (cq.Location, (loc.wrapped.Transformation(),))
    )

    for cls in (
        TopoDS_Shape,
        TopoDS_Compound,
        TopoDS_CompSolid,
        TopoDS_Solid,
        TopoDS_Shell,
        TopoDS_Face,
        TopoDS_Wire,
        TopoDS_Edge,
        TopoDS_Vertex,
    ):
        copyreg.pickle(cls, _reduce_topods)
