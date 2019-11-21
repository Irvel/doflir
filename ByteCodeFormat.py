from dataclasses import dataclass


@dataclass
class ByteCodeFormat(object):
    """docstring for ByteCodeFormat"""
    quads: list
    const_table: dict
    fun_dir: dict
