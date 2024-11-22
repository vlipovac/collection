"""Script module to draw UML-like class hierarchy graphs.

This module requires an installation of ``graphviz``.

1. Visit https://graphviz.org/download/ and download and install graphviz.
2. Run ``pip install graphviz`` and ``pip install pydot``.

The script takes the following source arguments:

- ``--source`` followed by a module name with namespace syntax
  (e.g. ``porepy.numerics.ad.operators``) and a class Name
- Multiple sequences of
  ``--source <module 1> <class 1> <class 2> .. --source <module 2> <class 3>``
  are supported

Examples:
    To plot the single phase flow model and its hierarchy, run the following

    ``python structure_chart.py porepy.models.fluid_mass_balance SinglePhaseFlow``

    To plot the SinglePhaseFlow and all methods in the hierarchy, add the ``-M`` flag

    ``python structure_chart.py porepy.models.fluid_mass_balance SinglePhaseFlow -M``

    To plot multiple the combined hierarchy of multiple classes contained in 1 module
    run

    ``python structure_chart.py porepy.models.fluid_mass_balance SinglePhaseFlow
    MassBalanceEquations``

    Though this makes little sense since the single phase flow inherits from Mass balance,
    but you get the idea.

    To plot sources and their hierarchies, you can run the following

    ``python structure_chart.py --source porepy.models.fluid_mass_balance
    SinglePhaseFlow --source porepy.models.mass_and_energy_balance
    MassAndEnergyBalance``

Note:
    Though the examples are mainly using porepy, any module, package and class works
    just as fine, as long as it can be imported by Python.

    For example, try ``python structure_chart.py sympy Symbol``, if you have sympy
    installed.

**Supported Flags:**

- ``-A`` to include abstract methods of classes
  (methods decorated with ``@abstractmethod`` in classes inheriting from ``abc.ABC``)
- ``-C`` to include class methods (methods decorated with ``@classmethod``)
- ``-D`` to include data attributes (on class level only)
- ``-M`` to include regular instance methods
- ``-P`` to include properties (methods decorated with ``@property``)
- ``-S`` to include static methods (methods decorated with ``@staticmethod``)
- ``--all-members`` to include all of the above
- ``--private`` to include private methods (methods beginning with a single ``_``)
- ``--magic`` to include magic overloads (methods beginning and ending with two ``__``)
- ``--render-engine`` followed by an engine name (see below).
- ``--exclude`` followed by names of classes to be excluded from the hierarchy. Python's
  base :obj:`object` is excluded by default.
- ``--show-module`` to show the full module namespace of a each class.

**Graphviz supported render engines:**

These are some examples of render engines. For more information, see documentation of
package :mod:`graphviz` or https://graphviz.org/docs/layouts/

- ``dot``: The default render engine, which is suitable for most graphs.
- ``neato``: A render engine that supports more advanced layout features, such as node
  positioning and edge layout.
- ``circo``: A render engine that is well-suited for circular layouts.
- ``twopi``: A render engine that is designed for radial layouts.
- ``fdp``: A render engine that is similar to neato, but with some additional features.
- ``sfdp``: A render engine that is designed for large graphs and is similar to fdp.
- ``osage``: Some advanced render engine.

Note:
    This is a simple script not fully utilizing capabilities of render engines.
    The changes are minimal. Circo, twopi and osage work kind of okay.

References:
    Basis for this code is found in
    https://codereview.stackexchange.com/questions/233604/
    draw-a-uml-style-class-hierarchy-of-pythons-abstract-base-classes-with-python

**Exit codes:**

When executed as main, following exit codes could be returned in the case if failure:

- 1: Failure to import graphviz (missing install)
- 2: Unknown or improper usage of flags
- 3: Unknown render engine
- 4: Missing argument after flag requiring additional argument(s)
- 5: Failed to import all of the provided sources (classes in modules)

"""

import sys
import warnings
from inspect import classify_class_attrs, isabstract
from typing import Any, Optional

try:
    from graphviz import Digraph  # type:ignore[import-untyped]
    from graphviz.backend.execute import (  # type:ignore[import-untyped]
        ExecutableNotFound,
    )
except ModuleNotFoundError:
    print("Error while import graphviz. Did you install it using pip install graphviz?")
    exit(1)


def section_template(
    section_name: str,
    section: Optional[list[str]] = None,
) -> str:
    if section:
        sec = f'<hr/><tr><td align="left"><b>{section_name}</b></td></tr>'
        sec_list = "<br/>".join(section)
        sec += f'<tr><td align="left" balign="left">{sec_list}</td></tr>'
        return sec
    else:
        return ""


def node_template(
    cls: type,
    fillcolor: str,
    show_module: bool,
    classmethods: Optional[list[str]] = None,
    data: Optional[list[str]] = None,
    methods: Optional[list[str]] = None,
    abstractmethods: Optional[list[str]] = None,
    properties: Optional[list[str]] = None,
    staticmethods: Optional[list[str]] = None,
    privatemethods: Optional[list[str]] = None,
    magicmethods: Optional[list[str]] = None,
) -> str:

    datasection: str = section_template("Data attributes", data)
    methodsection: str = section_template("Methods", methods)
    abstractsection: str = section_template("Abstract methods", abstractmethods)
    propertysection: str = section_template("Properties", properties)
    classsection: str = section_template("Class methods", classmethods)
    staticsection: str = section_template("Static methods", staticmethods)
    privatesection: str = section_template("Private members", privatemethods)
    magicsection: str = section_template("Magic members", magicmethods)

    if show_module:
        modulesection = f'<hr/><tr><td align="left"><b>{cls.__module__}</b></td></tr>'
    else:
        modulesection = ""

    header = f"""<
    <table border="1" cellborder="0" cellpadding="2" cellspacing="0" align="left"
    color="{fillcolor}">
    <tr><td align="center">
      <b>{'<i>{}</i>'.format(cls.__name__) if isabstract(cls) else cls.__name__}</b>
    </td></tr>
    {modulesection}
    """

    return (
        header
        + f"""
    {datasection}
    {propertysection}
    {methodsection}
    {abstractsection}
    {classsection}
    {staticsection}
    {privatesection}
    {magicsection}
    </table>>"""
    )


def node_label(
    cls: type,
    # include_abstractmethods: bool = False,
    # include_classmethods: bool = False,
    # include_data: bool = False,
    # include_methods: bool = False,
    # include_properties: bool = False,
    # include_staticmethods: bool = False,
    # include_privatemethods: bool = False,
    # include_magicmethods: bool = False,
    root: bool = False,
    show_module: bool = False,
) -> str:

    classmethods: list[str] = []
    data: list[str] = []
    methods: list[str] = []
    properties: list[str] = []
    staticmethods: list[str] = []
    privatemethods: list[str] = []
    magicmethods: list[str] = []

    # Only family of members for which there is a collective container
    abstractmethods = getattr(cls, "__abstractmethods__", [])

    for attr in classify_class_attrs(cls):
        # Show only if the attribute is defined in cls, not in any base class
        if attr.defining_class != cls:
            continue
        # NOTE by filtering private and magic methods, we exclude also all the
        # default members which every Python object has.
        # filtering magic methods
        if attr.name[:2] == "__" and attr.name[-2:] == "__":
            magicmethods.append(attr.name)
        # filtering private methods
        elif attr.name[0] == "_" and attr.name[1] != "_":
            privatemethods.append(attr.name)
        elif attr.kind == "data":
            data.append(attr.name)
        elif attr.kind == "method":
            methods.append(attr.name)
        elif attr.kind == "property":
            properties.append(attr.name)
        elif attr.kind == "class method":
            classmethods.append(attr.name)
        elif attr.kind == "static method":
            staticmethods.append(attr.name)
        else:
            warnings.warn(
                f"Uncovered class attribute kind detected: {(cls, attr.name, attr.kind)}",
                category=RuntimeWarning,
            )

    return node_template(
        cls=cls,
        fillcolor="red" if root else "black",
        show_module=show_module,
        classmethods=classmethods if include_classmethods else None,
        data=data if include_data else None,
        methods=methods if include_methods else None,
        abstractmethods=abstractmethods if include_abstractmethods else None,
        properties=properties if include_properties else None,
        staticmethods=staticmethods if include_staticmethods else None,
        privatemethods=privatemethods if include_privatemethods else None,
        magicmethods=magicmethods if include_magicmethods else None,
    )


def classtree_recursion(
    classes: list[type], all_classes: list[type], exclude: list[str]
) -> list[Any]:
    out: list[Any] = []
    for c in classes:
        if c.__name__ in exclude:
            continue
        if c not in all_classes:
            all_classes.append(c)
        if c.__bases__:
            out += [
                (c, classtree_recursion([p for p in c.__bases__], all_classes, exclude))
            ]
        else:
            out += [c]
    return out


def classtree(
    classes: list[type], exclude: list[str] | None = None
) -> tuple[list[Any], list[type]]:
    if exclude is None:
        exclude = []
    all_classes: list[type] = []
    tree = classtree_recursion(classes, all_classes, exclude)
    return tree, all_classes


def generate_dot(
    classtree: list[Any], engine: str = "dot", show_module: bool = False
) -> Digraph:

    # root classes from tree, which are given by the user input
    root_cls: list[type] = []
    for subtree in classtree:
        if isinstance(subtree, tuple):
            assert isinstance(subtree[0], type)
            root_cls.append(subtree[0])
        elif isinstance(subtree, type):
            root_cls.append(subtree)

    dot = Digraph(
        name=None,
        comment=None,
        filename=None,
        directory=None,
        format="svg",
        engine="fdp",
        encoding="utf-8",
        # graph_attr=None,
        graph_attr={"splines": "true"},
        node_attr=dict(shape="none"),
        edge_attr=dict(arrowtail="onormal", dir="back"),
        body=None,
        strict=True,
    )

    def recursion(classtree):
        for subtree in classtree:
            # Ignore the base for all classes
            # if subtree is object:
            #     pass
            # If we reach some leaf or stand-alone class, make it a node
            if isinstance(subtree, type):
                # if subtree is not object:
                dot.node(
                    subtree.__name__,
                    label=node_label(
                        subtree,
                        root=subtree in root_cls,
                        show_module=show_module,
                    ),
                )
            elif isinstance(subtree, tuple):
                cls, bases = subtree

                # draw class as node
                # if cls is not object:
                dot.node(
                    cls.__name__,
                    label=node_label(
                        cls,
                        root=cls in root_cls,
                        show_module=show_module,
                    ),
                )
                # call recursion for bases
                recursion(bases)
                # draw edges between bases and cls
                for b in bases:
                    # if b is object:
                    #     pass
                    if isinstance(b, tuple):
                        b_cls = b[0]
                        assert isinstance(b_cls, type)
                        # due to above recursion, b_cls should be a node
                        dot.edge(
                            b_cls.__name__,
                            cls.__name__,
                            style="dashed" if isabstract(b_cls) else "solid",
                            arrowhead="vee",
                            # arrowsize='2',
                        )

    recursion(classtree)
    return dot


if __name__ == "__main__":
    args = sys.argv

    member_flags = ["-A", "-C", "-D", "-M", "-P", "-S", "--private", "--magic"]
    other_flags = ["--all-members", "--render-engine", "--exclude", "--show-module"]
    engines = ["dot", "neato", "circo", "twopi", "fdp", "sfdp", "osage", "nop", "nop2"]

    args = args[1:]  # arg 0 is the file name

    # collective flag to draw all standard and public members
    all_members = "--all-members" in args
    if all_members:
        args.remove("--all-members")
        include_abstractmethods = True
        include_classmethods = True
        include_data = True
        include_magicmethods = False
        include_methods = True
        include_properties = True
        include_staticmethods = True
    else:
        # Parsing which class members are requested to be part of the chart
        include_abstractmethods = True if "-A" in args else False
        include_classmethods = True if "-C" in args else False
        include_data = True if "-D" in args else False
        include_methods = True if "-M" in args else False
        include_properties = True if "-P" in args else False
        include_staticmethods = True if "-S" in args else False

    # treat magic and private methods differently, because they can mess up the overview
    # These must be requested explicitely.
    include_magicmethods = True if "--magic" in args else False
    include_privatemethods = True if "--private" in args else False

    # Removing flags from args
    for f in member_flags:
        if f in args:
            args.remove(f)
        # if still in args, exit with error code
        if f in args:
            print(f"Flag {f} cannot be passed twice.")
            exit(2)

    # get engine definition
    engine: str = "dot"  # default engine
    if "--render-engine" in args:
        i = args.index("--render-engine") + 1
        if i >= len(args):
            print("Missing render engine argument after --render-engine.")
            exit(4)
        engine = args[i]
        if engine not in engines:
            print(f"Unknown render engine {engine}.")
            exit(3)
        args.remove("--render-engine")
        args.remove(engine)

    # get excluded classes
    excluded_cls: list[str] = []
    if "--exclude" in args:
        i = args.index("--exclude") + 1
        if i >= len(args):
            print("Missing class name(s) after --exclude.")
            exit(4)
        for a in args[i:]:
            if a[0] != "-":
                excluded_cls.append(a)
            else:
                break
        if len(excluded_cls) == 0:
            print("Missing class name(s) after --exclude.")
            exit(4)
        args.remove("--exclude")
        for a in excluded_cls:
            args.remove(a)
    # object is by default excluded
    excluded_cls.append("object")

    # get the show module flag
    if "--show-module" in args:
        show_module = True
        args.remove("--show-module")
    else:
        show_module = False

    # assert sane, remaining input
    for a in engines + member_flags + other_flags:
        if a in args:
            print(f"Cannot pass argument {a} twice.")
            exit(2)
    for a in args:
        if a[0] == "-" and a != "--source":
            print(f"Unknown flag {a}.")
            exit(2)

    # basic validation of input for module and classes: At least 1 module and 1 class
    # must be given.
    assert len(args) >= 2, "Require at least 1 module and 1 class as input."

    # argument for class tree construction, to be inferred from script arguments
    classes: list[type] = []
    class_names: list[str] = []
    # list of user-provided source modules and classes per module
    source_modules: list[str] = []
    source_classes: list[list[str]] = []

    # Multi module charting using multiple target modules and classes
    if "--source" in args:
        source_idx = [i for i, x in enumerate(args) if x == "--source"]
        for i in source_idx:
            module = args[i + 1]
            assert module != "--source", "Require module name after --source"
            cls = args[i + 2 :]
            # cut off class names before next --source
            if "--source" in cls:
                cls = cls[: cls.index("--source")]
            assert len(cls) > 0, f"Require class names after --source {module}"

            source_modules.append(module)
            source_classes.append(cls)
    # single module charting
    else:
        source_modules.append(args[0])
        source_classes.append(args[1:])

    # Loading classes from source modules
    failed_imports: list[str] = []
    for module, class_list in zip(source_modules, source_classes):
        if len(class_list) == 1:
            s = f"from {module} import {class_list[0]}"
        # by logic, there are more than 1 classes
        else:
            s = f"from {module} import " + ",".join(class_list)

        # dynamically load classes
        print(f"Loading from module {module}..")
        try:
            exec(s)
        # catch this error, since it is most likely raised by user input
        except ModuleNotFoundError:
            failed_imports.append(f"[{class_list}] from module {module}")
            continue

        # accessing the dynamically loaded objects
        for c in class_list:
            ct = globals()[c]
            if not isinstance(ct, type):
                failed_imports.append(f"'{c}' in module '{module}' is not a class.")
            else:
                classes.append(ct)
    # Warn about which import failed
    if failed_imports:
        print("Failure during import:\n" + "\n".join(failed_imports))
        # If all imports failed (no classes), exit
        if not classes:
            print("Could not import any of the given classes")
            exit(5)

    # Creating class tree and graph object
    print(f"Loaded classes:\n\t" + "\n\t".join([str(c) for c in classes]))
    print(f"Selected render engine: {engine}")
    print(f"Classes excluded from hierarchy: {excluded_cls}")
    clstree, all_cls = classtree(classes, exclude=excluded_cls)
    dot: Digraph = generate_dot(clstree, engine=engine, show_module=show_module)
    dot = dot.unflatten(stagger=3, fanout=True)
    # storing image
    try:
        dot.render("class_chart", format="svg")
        dot.render("class_chart", format="png")
    except ExecutableNotFound:
        print("Is Graphviz installed?\nhttps://graphviz.org/download/")
        exit(1)
