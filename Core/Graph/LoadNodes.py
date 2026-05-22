import pkgutil
import importlib

import Core.Nodes


def load_all_nodes():
    """
    Import semua module di folder Core.Nodes
    supaya decorator @register_node terpanggil.
    """

    package = Core.Nodes

    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__,
        package.__name__ + "."
    ):
        importlib.import_module(module_name)