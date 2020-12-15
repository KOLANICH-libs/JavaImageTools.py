import typing
from enum import IntEnum

import numpy as np
from JAbs import ClassesImportSpecT, ClassPathT, SelectedJVMInitializer
from jpype import JInt  # ToDo: JPype specific, create an abstraction in JAbs

ji = None  # initialized externally


def restack(npArr: np.ndarray, perm: typing.Iterable[int]) -> np.ndarray:
	compsSplitted = np.moveaxis(npArr, -1, 0)
	permed = []
	for el in perm:
		permed.append(compsSplitted[el])
	return np.dstack(permed)


def convertJavaEnum(namespace, prefix: str, name: str, enumCls: typing.Type[IntEnum] = IntEnum) -> typing.Type[IntEnum]:
	return enumCls(name, {el[len(prefix) :]: getattr(namespace, el) for el in dir(namespace) if el.startswith(prefix)})


class JavaImageToolsInitializer:
	__slots__ = ("ji", "scalaVersion")

	def __init__(self, classPathz: ClassPathT, classes2import: ClassesImportSpecT) -> None:
		self.__class__.ji.__set__(self, SelectedJVMInitializer(classPathz, classes2import))
		self.loadClasses(("java.awt.image.BufferedImage", "javax.imageio.ImageIO", "java.io.File", "java.awt.image.DataBufferByte"))
		self.ji.ImageMode = convertJavaEnum(self.ji.BufferedImage, "TYPE_", "ImageMode")
		self.modeRemapping = {
			"RGB": (self.ImageMode.INT_RGB, None),
			"RGBA": (self.ImageMode["4BYTE_ABGR"], (3, 2, 1, 0)),
			"1": (self.ImageMode.BYTE_BINARY, None),
			"L": (self.ImageMode.BYTE_GRAY, None),
			"I;16": (self.ImageMode.USHORT_GRAY, None),
			"BGR;32": (self.ImageMode.INT_BGR, None)
		}

	def __getattr__(self, k: str) -> typing.Any:
		return getattr(self.ji, k)

	def __setattr__(self, k: str, v: typing.Any):
		setattr(self.ji, k, v)

	def pilImg2JavaImg(self, img):
		i = np.array(img)
		jMode, remap = self.modeRemapping[img.mode]
		# t = self.ImageMode()
		if remap:
			i = restack(i, remap)
		iJ = self.ji.BufferedImage(i.shape[1], i.shape[0], jMode)
		raster = iJ.getData()
		raster.setPixels(0, 0, i.shape[1], i.shape[0], JInt[:](bytes(i.data)))
		iJ.setData(raster)
		return iJ
